#
# Copyright (c) 2017 Mycroft AI, Inc.
#
# This file is part of Mycroft Light
# (see https://github.com/MatthewScholefield/mycroft-light).
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#
import audioop
from abc import abstractmethod, ABCMeta
from threading import Event

import pyaudio
from speech_recognition import AudioData

from mycroft.util.text import to_snake


class MycroftListener(metaclass=ABCMeta):
    def __init__(self, global_config):
        config = global_config['listener']
        self.listener_config = config
        self.config = config.get(to_snake(self.__class__.__name__))

        self.chunk_size = config['chunk_size']
        self.format = pyaudio.paInt16
        self.sample_width = pyaudio.get_sample_size(self.format)
        self.sample_rate = config['sample_rate']
        self.channels = config['channels']

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.format, channels=self.channels,
                                  rate=self.sample_rate, input=True, frames_per_buffer=self.chunk_size)

        self.buffer_sec = config['wake_word_length']
        self.talking_volume_ratio = config['talking_volume_ratio']
        self.required_integral = config['required_noise_integral']
        self.max_di_dt = config['max_di_dt']
        self.noise_max_out_sec = config['noise_max_out_sec']
        self.sec_between_ww_checks = config['sec_between_ww_checks']
        self.recording_timeout = config['recording_timeout']
        self.energy_weight = 1.0 - pow(1.0 - config['ambient_adjust_speed'], self.chunk_size / self.sample_rate)

        # For convenience
        self.chunk_sec = self.chunk_size / self.sample_rate

        self.av_energy = None
        self.integral = 0
        self.noise_level = 0
        self.exit = False
        self.exit_event = Event()
        self.skip_wait = False

    def activate(self):
        self.skip_wait = True

    def _save_wav(self, raw_audio, name):
        """Save raw audio as wave file for debugging"""
        import wave
        wf = wave.open(name, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.sample_width)
        wf.setframerate(self.sample_rate)
        wf.writeframes(raw_audio)
        wf.close()

    def _calc_energy(self, sound_chunk):
        """Calculates how loud the sound is"""
        return audioop.rms(sound_chunk, self.sample_width)

    def wait_for_wake_word(self):
        """Listens to the microphone and returns when it hears the wake word"""
        self.av_energy = self._calc_energy(self.stream.read(self.chunk_size))

        buffer_size = int(self.sample_rate * self.buffer_sec * self.sample_width)
        raw_audio = b'\0' * buffer_size

        since_check = 0
        found_ww = False
        while not found_ww and not self.skip_wait:

            chunk = self.stream.read(self.chunk_size)
            raw_audio = raw_audio[-(buffer_size - len(chunk)):] + chunk
            self.update_energy(self._calc_energy(chunk))

            since_check += self.chunk_sec
            if since_check >= self.sec_between_ww_checks:
                since_check -= self.sec_between_ww_checks
                found_ww = self.found_wake_word(raw_audio)

            if self.exit:
                self.exit_event.set()
                raise SystemExit
        self.skip_wait = False

    def update_energy(self, energy):
        """Updates internal state with energy. Calculates average energy, noise level, and integral"""
        if energy > self.av_energy * self.talking_volume_ratio:
            self.noise_level += self.chunk_sec
            energy /= self.talking_volume_ratio
        else:
            self.noise_level -= self.chunk_sec / 2.0

        self.noise_level = max(0, min(self.noise_max_out_sec, self.noise_level))

        self.av_energy += (energy - self.av_energy) * self.energy_weight
        if self.av_energy != 0:
            di = max(0.0, energy / self.av_energy - 1.0) * self.chunk_size / self.sample_rate
            dt = self.chunk_sec
            if di / dt > self.max_di_dt:
                di = dt * self.max_di_dt
            self.integral += di

    def record_phrase(self):
        """
        Records until a period of silence
        :rtype: AudioData
        """
        raw_audio = b'\0' * self.sample_width
        self.integral = 0
        self.noise_level = 0
        total_sec = 0
        while total_sec < self.recording_timeout:
            if self.exit:
                self.exit_event.set()
                break
            chunk = self.stream.read(self.chunk_size)
            raw_audio += chunk
            total_sec += self.chunk_sec
            energy = self._calc_energy(chunk)
            self.update_energy(energy)
            if self.integral > self.required_integral and self.noise_level == 0:
                break

        return AudioData(raw_audio, self.sample_rate, self.sample_width)

    def on_exit(self):
        self.exit = True
        self.exit_event.wait()
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

    @abstractmethod
    def found_wake_word(self, raw_audio):
        pass
