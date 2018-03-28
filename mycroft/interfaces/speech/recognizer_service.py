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
import audioop

import pyaudio
from speech_recognition import AudioData

from mycroft.base_plugin import BasePlugin
from mycroft.interfaces.speech.wake_word_engines.wake_word_engine_plugin import WakeWordEnginePlugin
from mycroft.interfaces.speech.wake_word_service import WakeWordService
from mycroft.util import log


class RecognizerService(BasePlugin):
    def __init__(self, rt):
        super().__init__(rt)
        config = rt.config['interfaces']['speech']['recognizer']
        self.chunk_size = config['chunk_size']
        self.format = pyaudio.paInt16
        self.sample_width = pyaudio.get_sample_size(self.format)
        self.sample_rate = config['sample_rate']
        self.channels = config['channels']

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.format, channels=self.channels,
                                  rate=self.sample_rate, input=True,
                                  frames_per_buffer=self.chunk_size)

        self.talking_volume_ratio = config['talking_volume_ratio']
        self.required_integral = config['required_noise_integral']
        self.max_di_dt = config['max_di_dt']
        self.noise_max_out_sec = config['noise_max_out_sec']
        self.recording_timeout = config['recording_timeout']
        self.energy_weight = 1.0 - pow(1.0 - config['ambient_adjust_speed'],
                                       self.chunk_size / self.sample_rate)

        # For convenience
        self.chunk_sec = self.chunk_size / self.sample_rate

        self.av_energy = None
        self.integral = 0
        self.noise_level = 0
        self._intercept = None
        self._has_activated = False
        self.engine = WakeWordService(rt, self.on_activation)  # type: WakeWordEnginePlugin
        self.engine.startup()

    def intercept(self, exception):
        self._intercept = exception

    def _check_intercept(self):
        if self._intercept:
            exception = self._intercept
            self._intercept = None
            raise exception

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
        log.info('Waiting for wake word...')
        self.av_energy = self._calc_energy(self.stream.read(self.chunk_size))
        self.engine.continue_listening()

        while not self._has_activated:
            self._check_intercept()
            chunk = self.stream.read(self.chunk_size)
            self.update_energy(self._calc_energy(chunk))
            self.engine.update(chunk)

        self._has_activated = False
        self.engine.pause_listening()

    def update_energy(self, energy):
        """Updates internal state with energy. Calcs average energy, noise level, and integral"""
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

    def record_phrase(self) -> AudioData:
        """Records until a period of silence"""
        log.info('Recording...')
        raw_audio = b'\0' * self.sample_width
        self.integral = 0
        self.noise_level = 0
        total_sec = 0
        while total_sec < self.recording_timeout:
            self._check_intercept()
            chunk = self.stream.read(self.chunk_size)
            raw_audio += chunk
            total_sec += self.chunk_sec
            energy = self._calc_energy(chunk)
            self.update_energy(energy)
            if self.integral > self.required_integral and self.noise_level == 0:
                break

        log.info('Done recording.')
        return AudioData(raw_audio, self.sample_rate, self.sample_width)

    def on_exit(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
        self.engine.shutdown()

    def on_activation(self):
        """Called by child classes"""
        log.info('Heard wake word!')
        self._has_activated = True
