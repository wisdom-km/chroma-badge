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
    const uint64_t mask = (1ULL << pins::NFC_GPO) | (1ULL << pins::BOOT_n);
    esp_deep_sleep_enable_gpio_wakeup(mask, ESP_GPIO_WAKEUP_GPIO_LOW);
    Serial.println("sleep: wake on NFC_GPO or BOOT");
    Serial.flush();
    delay(20);
    esp_deep_sleep_start();
}

}  // namespace

void setup() {
    Serial.begin(115200);
    delay(400);
    Serial.println();
    Serial.println("BADGE-42C firmware v0.1");

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

    // Hold BOOT at reset to run a white-panel self-test; otherwise just blink and sleep.
    if (digitalRead(pins::BOOT_n) == LOW) {
        Serial.println("BOOT held: EPD OTP white refresh");
        led(true);
        bool ok = epd::refresh_solid(epd::Color::White);
        Serial.println(ok ? "EPD refresh done" : "EPD refresh TIMEOUT");
        led(false);
    } else {
        blink(3);
    }

    go_sleep();
}

void loop() {}
