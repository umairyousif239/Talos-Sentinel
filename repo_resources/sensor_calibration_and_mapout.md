## ESP32 Pinout Mapping

| Component | Sensor Pin | ESP32 GPIO Pin | Protocol / Logic |
| :--- | :--- | :--- | :--- |
| **AMG8833 Thermal** | SDA (Data) | **GPIO 27** | I2C Protocol |
| | SCL (Clock) | **GPIO 26** | I2C Protocol |
| **Flame IR Sensor** | DO (Digital Out) | **GPIO 25** | Active LOW (Binary) |
| **MQ-135 Gas Sensor** | A0 (Analog Out) | **GPIO 34** | 12-bit ADC (0-1800) |

## Calibration & Electrical Safety

### 1. Analog Voltage Scaling (MQ-135)
The **MQ-135 Gas Sensor** operates on a 5V logic level, but the **ESP32 ADC pins** are only rated for **3.3V**. Connecting the sensor directly would risk damaging the micro-controller or causing inaccurate "clipping" of high-concentration gas data.

To resolve this, a resistive voltage divider was implemented:
* **Resistor 1** ($R_1$): $10k\Omega$
* **Resistor 2** ($R_2$): $20k\Omega$

The output voltage ($V_{out}$) sent to **GPIO 34** is calculated as:
$$V_{out} = V_{in} \cdot \left( \frac{R_2}{R_1 + R_2} \right)$$
With a max $V_{in}$ of 5V, the $V_{out}$ is scaled to approximately **3.33V**, perfectly matching the ESP32's safe operating range.
### 2. MQ-135 "Burn-In" Phase
The MQ-135 utilizes a heating element to detect gases. For accurate readings:
* **Initial Pre-heat:** The sensor requires a one-time **24-hour "burn-in"** period to stabilize the internal chemical coating.
* **Operational Warm-up:** Upon every system boot, the firmware ignores the first **60 seconds** of gas data to allow the heater to reach a stable operating temperature.
### 3. Thermal Noise Filtering (AMG8833)
The AMG8833 8x8 grid can fluctuate due to ambient air currents.
* **Software Filter:** The **Mathematical Fusion Engine** applies a $0.5^{\circ}C$ dead-zone filter to the raw I2C data.
* **Differential Detection:** The system prioritizes the **Rate of Rise (RoR)** rather than a static temperature to distinguish between a person's body heat and a developing fire.