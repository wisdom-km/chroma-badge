#include "epd.h"
#include "nfc.h"
#include "pins.h"

#include <Arduino.h>
#include <esp_sleep.h>

namespace {

void led(bool on) { digitalWrite(pins::LED_STAT_n, on ? LOW : HIGH); }

float vbat_volts() {
    // 1M/1M divider, 12-bit ADC, 11 dB attenuation ~ 0..2.5 V at pin.
    analogSetPinAttenuation(pins::BAT_SENSE, ADC_11db);
    uint32_t acc = 0;
    for (int i = 0; i < 8; i++) {
        acc += analogReadMilliVolts(pins::BAT_SENSE);
    }
    return (acc / 8.0f) * 2.0f / 1000.0f;
}

void blink(int n) {
    for (int i = 0; i < n; i++) {
        led(true);
        delay(80);
        led(false);
        delay(80);
    }
}

void go_sleep() {
    pinMode(pins::NFC_GPO, INPUT_PULLUP);
    pinMode(pins::BOOT_n, INPUT_PULLUP);
    digitalWrite(pins::EPD_PWR_EN, HIGH);
    gpio_hold_en(pins::GPIO_PWR_EN);
    gpio_deep_sleep_hold_en();
    // IDF 4.4.7 light-sleep/deep-sleep GPIO wake is GPIO0–5 only.
    // GPIO9 is strapping / ROM download, not a deep-sleep wake source.
    const uint64_t mask = (1ULL << pins::NFC_GPO);
    esp_err_t err = esp_deep_sleep_enable_gpio_wakeup(mask, ESP_GPIO_WAKEUP_GPIO_LOW);
    if (err != ESP_OK) {
        Serial.printf("sleep: gpio wakeup failed (%d)\n", static_cast<int>(err));
    } else {
        Serial.println("sleep: wake on NFC_GPO (GPIO1)");
    }
    Serial.flush();
    delay(20);
    esp_deep_sleep_start();
}

}  // namespace

void setup() {
    Serial.begin(115200);
    delay(400);
    Serial.println();
    Serial.println("BADGE-42C firmware v0.2");

    pinMode(pins::LED_STAT_n, OUTPUT);
    led(false);
    pinMode(pins::BOOT_n, INPUT_PULLUP);
    pinMode(pins::NFC_GPO, INPUT_PULLUP);

    epd::begin();
    nfc::begin();

    Serial.printf("VBAT ~ %.2f V\n", vbat_volts());
    Serial.printf("ST25DV %s at 0x%02X\n", nfc::present() ? "ACK" : "no ACK", nfc::ADDR_USER);
    Serial.printf("BOOT=%d GPO=%d\n", digitalRead(pins::BOOT_n), digitalRead(pins::NFC_GPO));

    gpio_hold_dis(pins::GPIO_PWR_EN);
    gpio_deep_sleep_hold_dis();

    // ROM download: hold BOOT (GPIO9) through RESET. Do not treat that as EPD self-test.
    uint32_t wait_cdc = millis();
    while (!Serial && (millis() - wait_cdc) < 8000) {
        delay(10);
    }
    Serial.println("send W within 5s for EPD white self-test");
    Serial.flush();
    bool want_white = false;
    uint32_t t0 = millis();
    while (millis() - t0 < 5000) {
        if (Serial.available()) {
            char c = static_cast<char>(Serial.read());
            if (c == 'W' || c == 'w') {
                want_white = true;
                break;
            }
        }
        delay(10);
    }

    if (want_white) {
        Serial.println("serial W: EPD OTP white refresh");
        led(true);
        bool ok = epd::refresh_solid(epd::Color::White);
        if (ok) {
            Serial.println("EPD refresh done");
        } else {
            Serial.printf("EPD refresh TIMEOUT at %s\n",
                          epd::last_fail[0] ? epd::last_fail : "unknown");
        }
        led(false);
    } else {
        blink(3);
    }

    go_sleep();
}

void loop() {}
