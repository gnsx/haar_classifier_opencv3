git clone https://github.com/FFmpeg/FFmpeg.git
cd FFmpeg
sudo ./configure --arch=armel --target-os=linux --enable-gpl --enable-omx --enable-omx-rpi --enable-nonfree --enable-network --enable-protocol=tcp --enable-demuxer=rtsp
sudo make -j4
sudo make install