---
layout: page
title: Projects
featured_image: assets/images/pages/projects.jpg
copyright: 2021
---

Image by <a href="https://pixabay.com/users/seven11nash-3644229/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=1784564">Marc Mueller</a> from <a href="https://pixabay.com/?utm_source=link-attribution&amp;utm_medium=referral&amp;utm_campaign=image&amp;utm_content=1784564">Pixabay</a>

## espMqttClient

espMqttClient is an MQTT client library for the Arduino framework, made for ESP8266 and ESP32. With little effort, other platforms can be supported as well.

MQTT was the choise I made for communication with my IoT devices. And as a fan of non-blocking code (or even better, asynchronous code), I relied on Async-mqtt-client. It has been my go-to MQTT client for many years. It was fast, reliable and had features that were non-existing in alternative libraries. However, the underlying async TCP libraries are lacking updates, especially updates related to secure connections. I eventually decided to write my own library, from scratch (I copied the API though). [This is the result](https://github.com/bertmelis/espMqttClient).

## VitoWiFi

Arduino Library for ESP8266 to communicate with Viessmann boilers using a (DIY) serial optolink.

Based on the fantastic work on openv. Check out this wiki for a simple hardware implementations

You can find my library here: [https://github.com/bertmelis/VitoWiFi](https://github.com/bertmelis/VitoWiFi).

## eModbus

Joint project to bring a compliant modbus server and client to ESP32 for RTU and TCP.

Read the docs at [https://emodbus.github.io](https://emodbus.github.io).

## esp32WS2811

My library is an Arduino library for ESP32 to drive WS2811 LEDs using the RMT peripheral on ESP32 microcontrollers.

It is a wrapper library around the WS2811 driver written by @nkolban, published on [his Github account](https://github.com/nkolban/esp32-snippets).

You can find my library here: [https://github.com/bertmelis/esp32WS2811](https://github.com/bertmelis/esp32WS2811).

A full blown demo application is available here: [https://github.com/bertmelis/ledController](https://github.com/bertmelis/ledController).

## async-mqtt-client

async-mqtt-client is a Arduino MQTT library for ESP8266 and ESP32. Altough not my project, I did try to improve the library significantly.

you can find the code here: [https://github.com/marvinroger/async-mqtt-client](https://github.com/marvinroger/async-mqtt-client).
