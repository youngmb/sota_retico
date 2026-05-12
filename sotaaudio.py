"""
Sota Audio Module
============
-- modified from the retico standard audio.py module

This module defines basic incremental units and incremental modules to handle
audio input and output via the Sota
"""

import queue
import platform
import pyaudio
import retico_core
from retico_core.audio import AudioIU
from sota_thinclient import ConnectionManager

CHANNELS = 1
"""Number of channels. For now, this is hard coded MONO. If there is interest to do
stereo or audio with even more channels, it has to be integrated into the modules."""

class SotaMicrophoneModule(retico_core.AbstractProducingModule):

    """A module that produces IUs containing audio signals incoming from a Sota via the sota_thinclient module,
       streamed over a network."""

    @staticmethod
    def name():
        return "Sota Microphone Module"

    @staticmethod
    def description():
        return "A producing module that provides audio from a Sota robot, streamed over udp."

    @staticmethod
    def output_iu():
        return AudioIU

    def callback(self, in_data, frame_count, time_info, status):
        """The callback function that gets called by pyaudio.

        Args:
            in_data (bytes[]): The raw audio that is coming in from the
                microphone
            frame_count (int): The number of frames that are stored in in_data
        """
        self.audio_buffer.put(in_data)
        return (in_data, pyaudio.paContinue)

    def __init__(self, sota: ConnectionManager, data_udp_port: int, **kwargs):
        """
        Initialize the Sota Microphone Module.

        Args:
            frame_length (float): The length of one frame (i.e., IU) in seconds
            rate (int): The frame rate of the recording
            sample_width (int): The width of a single sample of audio in bytes.
            device_index (int): The device index of the microphone to use. If None,
                uses the default input device.
        """
        super().__init__(**kwargs)
        self.sota = sota

        self.frame_length = None
        self.rate = None
        self.sample_width = None
        self.data_udp_port = data_udp_port

        self.audio_buffer = sota.microphone.data_queue
        self.chunk_size_in_frames = None

    def process_update(self, _):
        if not self.audio_buffer:
            return None
        try:
            sample = self.audio_buffer.get(timeout=1.0)
        except queue.Empty:
            return None
        output_iu = self.create_iu()
        output_iu.set_audio(sample, self.chunk_size_in_frames, self.rate, self.sample_width)
        return retico_core.UpdateMessage.from_iu(output_iu, retico_core.UpdateType.ADD)

    def setup(self):
        """Set up the microphone for recording."""
        self.sota.microphone.enable(data_udp_port=self.data_udp_port, restart_if_enabled=True)
        sota_state = self.sota.microphone.get_state(use_cached=True)
        self.rate = sota_state['sampleRate']
        self.sample_width = sota_state['sampleSize_bits'] // 8
        self.chunk_size_in_frames = sota_state['bufferSize'] // self.sample_width
        print(sota_state)

    def prepare_run(self):
        pass

    def shutdown(self):
        self.sota.microphone.disable()

#
# class SpeakerModule(retico_core.AbstractConsumingModule):
#     """A module that consumes AudioIUs of arbitrary size and outputs them to the
#     speakers of the machine. When a new IU is incoming, the module blocks as
#     long as the current IU is being played."""
#
#     @staticmethod
#     def name():
#         return "Speaker Module"
#
#     @staticmethod
#     def description():
#         return "A consuming module that plays audio from speakers."
#
#     @staticmethod
#     def input_ius():
#         return [AudioIU]
#
#     @staticmethod
#     def output_iu():
#         return None
#
#     def __init__(
#         self,
#         rate=44100,
#         sample_width=2,
#         use_speaker="both",
#         device_index=None,
#         **kwargs
#     ):
#         super().__init__(**kwargs)
#         self.rate = rate
#         self.sample_width = sample_width
#         self.use_speaker = use_speaker
#
#         self._p = pyaudio.PyAudio()
#
#         if device_index is None:
#             device_index = self._p.get_default_output_device_info()["index"]
#         self.device_index = device_index
#
#         self.stream = None
#         self.time = None
#
#     def process_update(self, update_message):
#         for iu, ut in update_message:
#             if ut == retico_core.UpdateType.ADD:
#                 self.stream.write(bytes(iu.raw_audio))
#         return None
#
#     def setup(self):
#         """Set up the speaker for outputting audio"""
#         p = self._p
#
#         if platform.system() == "Darwin":
#             if self.use_speaker == "left":
#                 stream_info = pyaudio.PaMacCoreStreamInfo(channel_map=(0, -1))
#             elif self.use_speaker == "right":
#                 stream_info = pyaudio.PaMacCoreStreamInfo(channel_map=(-1, 0))
#             else:
#                 stream_info = pyaudio.PaMacCoreStreamInfo(channel_map=(0, 0))
#         else:
#             stream_info = None
#
#         self.stream = p.open(
#             format=p.get_format_from_width(self.sample_width),
#             channels=CHANNELS,
#             rate=self.rate,
#             input=False,
#             output_host_api_specific_stream_info=stream_info,
#             output=True,
#             output_device_index=self.device_index,
#         )
#
#     def shutdown(self):
#         """Close the audio stream."""
#         self.stream.stop_stream()
#         self.stream.close()
#         self.stream = None
#
#
# class StreamingSpeakerModule(retico_core.AbstractConsumingModule):
#     """A module that consumes Audio IUs and outputs them to the speaker of the
#     machine. The audio output is streamed and thus the Audio IUs have to have
#     exactly [chunk_size] samples."""
#
#     @staticmethod
#     def name():
#         return "Streaming Speaker Module"
#
#     @staticmethod
#     def description():
#         return "A consuming module that plays audio from speakers."
#
#     @staticmethod
#     def input_ius():
#         return [AudioIU]
#
#     @staticmethod
#     def output_iu():
#         return None
#
#     def callback(self, in_data, frame_count, time_info, status):
#         """The callback function that gets called by pyaudio."""
#         if self.audio_buffer:
#             try:
#                 audio_paket = self.audio_buffer.get(timeout=TIMEOUT)
#                 return (audio_paket, pyaudio.paContinue)
#             except queue.Empty:
#                 pass
#         return (b"\0" * frame_count * self.sample_width, pyaudio.paContinue)
#
#     def __init__(self, frame_length=0.02, rate=44100, sample_width=2, **kwargs):
#         """Initialize the streaming speaker module.
#
#         Args:
#             frame_length (float): The length of one frame (i.e., IU) in seconds.
#             rate (int): The frame rate of the audio. Defaults to 44100.
#             sample_width (int): The sample width of the audio. Defaults to 2.
#         """
#         super().__init__(**kwargs)
#         self.frame_length = frame_length
#         self.chunk_size = round(rate * frame_length)
#         self.rate = rate
#         self.sample_width = sample_width
#
#         self._p = pyaudio.PyAudio()
#
#         self.audio_buffer = queue.Queue()
#         self.stream = None
#
#     def process_update(self, update_message):
#         for iu, ut in update_message:
#             if ut == retico_core.UpdateType.ADD:
#                 self.audio_buffer.put(iu.raw_audio)
#         return None
#
#     def setup(self):
#         """Set up the speaker for speaking...?"""
#         p = self._p
#         self.stream = p.open(
#             format=p.get_format_from_width(self.sample_width),
#             channels=CHANNELS,
#             rate=self.rate,
#             input=False,
#             output=True,
#             stream_callback=self.callback,
#             frames_per_buffer=self.chunk_size,
#         )
#
#     def prepare_run(self):
#         self.stream.start_stream()
#
#     def shutdown(self):
#         """Close the audio stream."""
#         self.stream.stop_stream()
#         self.stream.close()
#         self.stream = None
#         self.audio_buffer = queue.Queue()
