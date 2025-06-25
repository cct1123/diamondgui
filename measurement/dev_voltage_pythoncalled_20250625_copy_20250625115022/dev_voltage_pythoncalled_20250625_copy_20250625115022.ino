bool running = false;
int dutyCycle = 50;  // in percent
const unsigned int period = 100;  // Total period in microseconds (10 kHz)

unsigned long lastToggleTime = 0;
bool pinState = false;

void setup() {
  pinMode(3, OUTPUT);
  digitalWrite(3, LOW);
  Serial.begin(9600);
}

void loop() {
  // Handle serial commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command == "H") {
      running = true;
    } else if (command == "pause" || command == "end") {
      running = false;
      digitalWrite(3, LOW);  // Turn off pin when stopping
    } else {
      int value = command.toInt();
      if (value >= 1 && value <= 100) {
        dutyCycle = value;
        Serial.print("Duty cycle set to ");
        Serial.print(dutyCycle);
        Serial.println("%");
      } else {
        Serial.println("Invalid duty cycle. Enter 1–100.");
      }
    }
  }

  // High-speed PWM logic
  if (running) {
    unsigned long now = micros();
    unsigned int onTime = period * dutyCycle / 100;
    unsigned int offTime = period - onTime;

    if (pinState && (now - lastToggleTime >= onTime)) {
      PORTD &= ~(1 << PD3);  // Set LOW
      pinState = false;
      lastToggleTime = now;
    } else if (!pinState && (now - lastToggleTime >= offTime)) {
      PORTD |= (1 << PD3);   // Set HIGH
      pinState = true;
      lastToggleTime = now;
    }
  }
}
