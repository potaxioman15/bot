import yt_dlp
import os

def descargar_video(url, formato="mp4"):
    """
    Descarga un video de YouTube u otra plataforma soportada por yt-dlp.
    formato: "mp4" para video completo, "mp3" para solo audio.
    Devuelve la ruta del archivo descargado.
    """
    # Carpeta temporal
    output_template = "descargas/%(title)s.%(ext)s"
    os.makedirs("descargas", exist_ok=True)

    ydl_opts = {
        'outtmpl': output_template,
        'quiet': False,  # Cambia a True para menos salida
    }

    if formato.lower() == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:  # mp4
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            filename = ydl.prepare_filename(info)
            if formato.lower() == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"
            print(f"✅ Descargado: {filename}")
            return filename
    except Exception as e:
        print(f"❌ Error al descargar: {e}")
        return None

# EJEMPLO DE USO
if __name__ == "__main__":
    url = input("Introduce la URL del video o canción: ")
    tipo = input("¿Deseas 'mp4' o 'mp3'? ").lower()
    archivo = descargar_video(url, tipo)
    if archivo:
        print(f"Archivo listo: {archivo}")

if __name__ == "__main__":
    url = input("Introduce la URL del video o canción: ")
    tipo = input("¿Deseas 'mp4' o 'mp3'? ").lower()
    archivo = descargar_video(url, tipo)
    if archivo:
        print(f"Archivo listo: {archivo}")

