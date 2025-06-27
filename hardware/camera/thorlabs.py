import base64
import threading
import time

import cv2
import numpy as np
from thorlabs_tsi_sdk.tl_camera import TLCameraSDK


class CameraController:
    def __init__(self):
        self.frame_data = None
        self.running = False
        self.lock = threading.Lock()
        self.last_frame_time = 0
        self.thread = None

    def update_frame(self, data):
        with self.lock:
            self.frame_data = data
            self.last_frame_time = time.time()

    def get_frame(self):
        with self.lock:
            return self.frame_data

    def is_running(self):
        with self.lock:
            return self.running

    def set_running(self, running: bool):
        with self.lock:
            self.running = running

    def start(self):
        if not self.is_running():
            self.set_running(True)
            self.thread = threading.Thread(target=self._run_camera_loop, daemon=True)
            self.thread.start()

    def stop(self):
        """
        Forcefully signals the camera thread to stop and returns immediately.
        This function does NOT wait for the thread to terminate. It acts as a
        "fire and forget" command to kill the thread as fast as possible from the
        caller's perspective. Use 'close()' for a graceful shutdown.
        """
        print("Forcefully stopping camera thread...")
        self.set_running(False)
        # We do not join the thread here to allow for an immediate return.
        # The background thread will clean up and exit on its own.

    def close(self):
        """
        Gracefully stops the camera acquisition thread and waits for it to
        cleanly disconnect. This is the recommended way to stop the camera.
        """
        print("Gracefully closing camera...")
        self.set_running(False)
        # Wait for the thread to finish, but only if it's alive
        thread = None
        with self.lock:
            thread = self.thread
        if thread and thread.is_alive():
            thread.join(timeout=2.0)
        print("Camera closed.")

    def _run_camera_loop(self):
        print("Starting camera thread")
        try:
            with TLCameraSDK() as sdk:
                available_cameras = sdk.discover_available_cameras()
                if not available_cameras:
                    print("No cameras found")
                    return

                print(f"Found camera: {available_cameras[0]}")
                with sdk.open_camera(available_cameras[0]) as camera:
                    print("Camera opened")
                    camera.roi = (
                        0,
                        0,
                        camera.sensor_width_pixels,
                        camera.sensor_height_pixels,
                    )
                    camera.exposure_time_us = 10000
                    camera.frames_per_trigger_zero_for_unlimited = 0
                    camera.image_poll_timeout_ms = 1000
                    camera.arm(2)
                    camera.issue_software_trigger()
                    print("Camera armed")

                    while self.is_running():
                        frame = camera.get_pending_frame_or_null()
                        if frame is None:
                            time.sleep(0.005)
                            continue

                        # --- Image processing ---
                        image_buffer = np.copy(frame.image_buffer)
                        grayscale_img = image_buffer.reshape(
                            camera.image_height_pixels,
                            camera.image_width_pixels,
                        )
                        if grayscale_img.max() > 0:
                            gray_8bit = cv2.convertScaleAbs(
                                grayscale_img,
                                alpha=(255.0 / grayscale_img.max()),
                            )
                        else:
                            gray_8bit = np.zeros_like(grayscale_img, dtype=np.uint8)
                        rgb_image = cv2.cvtColor(gray_8bit, cv2.COLOR_GRAY2RGB)
                        _, buffer = cv2.imencode(
                            ".jpg", rgb_image, [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                        )
                        jpg_as_text = base64.b64encode(buffer).decode("utf-8")
                        self.update_frame(jpg_as_text)

                    print("Disarming camera...")
                    camera.disarm()

        except Exception as e:
            print(f"Camera thread error: {e}")
        finally:
            print("Camera thread exiting")
            self.set_running(False)  # Ensure state is consistent
            with self.lock:
                self.thread = None


# -------------------- Test block --------------------
if __name__ == "__main__":
    print("--- Testing graceful close() ---")
    cam_close = CameraController()
    cam_close.start()
    time.sleep(2)  # Let camera run
    cam_close.close()
    print("Graceful close test finished.\n")

    time.sleep(1)  # Pause between tests

    print("--- Testing forceful stop() ---")
    cam_stop = CameraController()
    cam_stop.start()
    time.sleep(2)  # Let camera run
    cam_stop.stop()  # This returns immediately
    print("Forceful stop() returned control to main thread.")
    # The background thread is still shutting down, we can wait here to see the messages
    time.sleep(1)
    print("Forceful stop test finished.")
