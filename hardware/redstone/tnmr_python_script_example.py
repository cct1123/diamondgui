#                No-Tune AutoSweep Script                #
#    Adam Dioguardi at Los Alamos National Lab.          #
# ****************************************************** #
import math
import os
import time

import win32com.client


def NoTuneAutoSweep():
    global \
        start_freq, \
        end_freq, \
        step_freq, \
        # email_notification, \
        # to_addresses, \
        # subject, \
        # message

    global \
        run_sweep_bool, \
        elapsed_scan_time, \
        total_scan_time, \
        sweep_finished_bool, \
        abort_bool, \
        start_time

    NTNMR = win32com.client.Dispatch("NTNMR.Application")
    # open_file = NTNMR.GetActiveDocPath
    # path_name = os.path.dirname(open_file)
    # path_name_out = path_name + "\\stack"

    # if not os.path.exists(path_name_out):
    #     os.makedirs(path_name_out)

    OneScanTime = 0

    numberfreqs = int(2 + (end_freq - start_freq) / step_freq)

    # integration_file = open(path_name + "\\IntegrationResults.txt", "w")
    # integration_file.write("RealWave, ImagWave, MagWave, FreqWave\n")

    for i in range(1, numberfreqs):
        if abort_bool:
            abort_bool = False
            return

        if i == 1:
            start_time = time.time()

        NTNMR.SetNMRParameter("Observe Freq.", start_freq + (i - 1) * step_freq)
        NTNMR.ZG

        while not NTNMR.CheckAcquisition:
            time.sleep(1)

        # iterfreqfloat = float(start_freq + (i - 1) * step_freq)
        # iterfreqstr = "%07.3f" % iterfreqfloat
        # file_name_out = path_name_out + "\\notuneAS_" + iterfreqstr + "MHz" + ".tnt"
        # NTNMR.SaveAs(file_name_out)

        # intStart = NTNMR.GetCursorPosition
        # intEnd = NTNMR.Get1DSelectionEnd
        # nmrdata = NTNMR.GetData

        # realTotal = 0
        # imagTotal = 0

        # for j in range(intStart, intEnd * 2 - 1, 2):
        #     realTotal += nmrdata[j] / NTNMR.GetNMRParameter("Scans 1D")
        #     imagTotal += nmrdata[j + 1] / NTNMR.GetNMRParameter("Scans 1D")

        # magTotal = math.sqrt(pow(realTotal, 2) + pow(imagTotal, 2))

        # x_int = float((start_freq + (numberfreqs - 1) * step_freq) / 1000)

        # graphY.append(magTotal)
        # graphX.append(x_int)

        # integration_file.write(
        #     "%s, %s, %s, %s\n" % (realTotal, imagTotal, magTotal, x_int)
        # )

        # NTNMR.CloseFile(file_name_out)

        if i == 1:
            OneScanTime = time.time() - start_time
            total_scan_time = OneScanTime * (numberfreqs - 2)

    sweep_finished_bool = True
    # en = email_notifier()
    # if email_notification == 1:
    #     en.sendemail(to_addresses, subject, message)

    # integration_file.close()

    # Emmeline adds 
    print("Redstone Done!")
    print("Run time per freq:", OneScanTime)