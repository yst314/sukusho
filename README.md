ydl_opts内にproxyを書く

## ffmpeg
https://www.gyan.dev/ffmpeg/builds/
fullをダウンロードし環境変数のPATHにbin/を通す

## 実行速度
- インターバル 10秒
- [アロナチャンネル#2](https://youtu.be/OxoS3HiCjTs?si=wTVuE12CKkC7RS99)
- 1:53　6786フレーム
- RUSTでスクショ: 7.637008190155029
- PYTHONでスクショ: 32.93653416633606

pythonでクロップを指定したフレームに飛んでcaptureするコードに変更したところ実行速度が
インターバル10秒
- jpg 3.374500274658203
- png 3.6236729621887207

インターバル1秒
- jpg 25.06740403175354
- png 29.111324310302734
rustはffmpegを呼び出ししているが毎回動画を読み込んでいるので遅いらしい

cap.readが重いんだから、