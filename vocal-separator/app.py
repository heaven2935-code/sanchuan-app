"""音樂人聲分離工具 - Streamlit 前端。"""
from __future__ import annotations

import traceback
from pathlib import Path

import streamlit as st

import downloader
import file_manager
import mixer
import separator
from config import APP_NAME, DEFAULT_VOCAL_VOLUME_PERCENT, OUTPUT_FORMATS

st.set_page_config(page_title=APP_NAME, page_icon="🎤", layout="centered")

_FORMAT_LABELS = {"mp3": "MP3 320kbps", "wav": "WAV"}
_RESULT_LABELS = {
    "instrumental": "純伴唱版（無人聲）",
    "lead_vocal": "導唱版",
    "vocals_only": "純人聲版",
}


def render_dependency_check() -> bool:
    ffmpeg_ok = mixer.check_ffmpeg_available()
    ytdlp_ok = downloader.check_ytdlp_available()
    demucs_ok = separator.check_demucs_available()
    all_ok = ffmpeg_ok and ytdlp_ok and demucs_ok

    with st.expander("🔧 環境檢查", expanded=not all_ok):
        st.write(f"{'✅' if ffmpeg_ok else '❌'} FFmpeg（混音／轉檔／音量調整）")
        st.write(f"{'✅' if ytdlp_ok else '❌'} yt-dlp（網址下載）")
        st.write(f"{'✅' if demucs_ok else '❌'} Demucs / PyTorch（人聲分離）")

        if not all_ok:
            st.error("偵測到缺少必要元件，請依下列步驟安裝後重新啟動程式。")
            if not ffmpeg_ok:
                st.markdown(
                    "**缺少 FFmpeg**\n\n"
                    "Windows 安裝方式（擇一）：\n"
                    "- winget：`winget install --id Gyan.FFmpeg -e`\n"
                    "- Chocolatey：`choco install ffmpeg`\n"
                    "- 手動安裝：至 https://www.gyan.dev/ffmpeg/builds/ 下載完整版，"
                    "解壓縮後將其中的 `bin` 資料夾路徑加入系統環境變數 PATH，"
                    "然後重新開啟命令提示字元。\n"
                    "- 或直接執行專案內的 `install.bat` 自動檢查與提示。"
                )
            if not ytdlp_ok or not demucs_ok:
                st.markdown(
                    "**缺少 Python 套件（yt-dlp / demucs / torch）**\n\n"
                    "請在專案資料夾開啟命令提示字元，執行：\n"
                    "```\ninstall.bat\n```\n"
                    "或手動執行：\n"
                    "```\npython -m venv .venv\n"
                    ".venv\\Scripts\\activate\n"
                    "pip install -r requirements.txt\n"
                    "```"
                )
    return all_ok


def run_pipeline(job: file_manager.JobPaths, source_audio: Path, vocal_volume_percent: float, formats: tuple[str, ...]):
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    def make_callback(stage_start: float, stage_end: float):
        def cb(fraction: float, message: str) -> None:
            value = stage_start + (stage_end - stage_start) * max(0.0, min(1.0, fraction))
            progress_bar.progress(min(max(value, 0.0), 1.0))
            status_text.text(message)
        return cb

    stems = separator.separate(source_audio, job.stems_dir, progress_callback=make_callback(0.05, 0.8))
    outputs = mixer.render_outputs(
        stems, job.output_dir, vocal_volume_percent, formats=formats,
        progress_callback=make_callback(0.8, 1.0),
    )
    progress_bar.progress(1.0)
    status_text.text("處理完成！")
    return outputs


def render_results(job_id: str) -> None:
    result = st.session_state.get(f"result_{job_id}")
    if not result:
        return

    outputs = result["outputs"]
    used_volume = result["vocal_volume"]
    labels = dict(_RESULT_LABELS)
    labels["lead_vocal"] = f"導唱版（人聲音量 {used_volume}%）"

    st.subheader("📥 下載結果")
    for key, label in labels.items():
        available = [fmt for fmt in OUTPUT_FORMATS if f"{key}_{fmt}" in outputs]
        if not available:
            continue
        st.markdown(f"**{label}**")
        cols = st.columns(len(available))
        for col, fmt in zip(cols, available):
            path = Path(outputs[f"{key}_{fmt}"])
            if not path.exists():
                continue
            with col:
                st.download_button(
                    label=f"下載 {_FORMAT_LABELS[fmt]}",
                    data=path.read_bytes(),
                    file_name=f"{key}.{fmt}",
                    mime="audio/mpeg" if fmt == "mp3" else "audio/wav",
                    key=f"dl_{job_id}_{key}_{fmt}",
                )


def render_cleanup_panel() -> None:
    st.divider()
    st.subheader("🧹 清除暫存檔")
    jobs = file_manager.list_jobs()
    if not jobs:
        st.caption("目前沒有暫存檔案。")
        return

    total_size = sum(j["size_bytes"] for j in jobs)
    st.caption(f"共 {len(jobs)} 個工作暫存，佔用 {file_manager.human_readable_size(total_size)}")

    for job in jobs:
        c1, c2, c3 = st.columns([3, 2, 1])
        c1.text(job["job_id"])
        c2.text(file_manager.human_readable_size(job["size_bytes"]))
        if c3.button("刪除", key=f"del_{job['job_id']}"):
            file_manager.cleanup_job(job["job_id"])
            st.rerun()

    if st.button("清除全部暫存檔"):
        n = file_manager.cleanup_all()
        st.success(f"已清除 {n} 個暫存工作")
        st.rerun()


def main() -> None:
    st.title(f"🎤 {APP_NAME}")
    st.caption("將音樂分離為人聲與伴奏，產生純伴唱版、導唱版與純人聲版。僅限本機處理。")
    st.info(
        "⚠️ 本工具僅供處理您擁有合法使用權（自行創作、已取得授權或版權方允許）的音樂內容。"
        "本工具不會、也不允許用於繞過 DRM 保護、付費牆或登入限制取得受限內容。",
        icon="⚠️",
    )

    all_ok = render_dependency_check()

    tab_url, tab_upload = st.tabs(["🔗 貼上網址", "📁 上傳檔案"])
    with tab_url:
        url_value = st.text_input("影音網址（yt-dlp 支援的網站）", key="url_input")
    with tab_upload:
        uploaded_file = st.file_uploader("上傳音訊／影片檔案", type=["mp3", "wav", "m4a", "mp4"])

    vocal_volume = st.slider("導唱人聲音量 (%)", min_value=0, max_value=100, value=DEFAULT_VOCAL_VOLUME_PERCENT)
    formats = st.multiselect(
        "輸出格式", options=list(OUTPUT_FORMATS), default=list(OUTPUT_FORMATS),
        format_func=lambda f: _FORMAT_LABELS[f],
    )

    start = st.button("🚀 開始處理", type="primary", disabled=not all_ok)

    if start:
        if not formats:
            st.error("請至少選擇一種輸出格式")
            return
        if not url_value and uploaded_file is None:
            st.error("請輸入網址或上傳檔案")
            return

        job = file_manager.create_job()
        st.session_state["current_job_id"] = job.job_id

        try:
            with st.spinner("準備音訊來源…"):
                if uploaded_file is not None:
                    raw_path = file_manager.save_uploaded_file(job, uploaded_file.name, uploaded_file.getvalue())
                    source_audio = job.input_dir / "source.wav"
                    mixer.convert_to_wav(raw_path, source_audio)
                else:
                    source_audio = downloader.download_audio(url_value, job.input_dir)

            outputs = run_pipeline(job, source_audio, vocal_volume, tuple(formats))
            st.session_state[f"result_{job.job_id}"] = {
                "outputs": {k: str(v) for k, v in outputs.items()},
                "vocal_volume": vocal_volume,
            }
            st.success("✅ 處理完成，請於下方下載結果。")

        except downloader.RestrictedContentError as exc:
            st.error(f"🚫 {exc}")
            file_manager.cleanup_job(job.job_id)
            st.session_state.pop("current_job_id", None)
        except (downloader.DownloadError, separator.SeparationError, mixer.MixError) as exc:
            st.error(f"❌ 處理失敗：{exc}")
            file_manager.cleanup_job(job.job_id)
            st.session_state.pop("current_job_id", None)
        except Exception as exc:  # noqa: BLE001 保底錯誤處理，避免畫面直接崩潰
            st.error(f"❌ 發生未預期錯誤：{exc}")
            with st.expander("錯誤詳細資訊"):
                st.code(traceback.format_exc())
            file_manager.cleanup_job(job.job_id)
            st.session_state.pop("current_job_id", None)

    current_job_id = st.session_state.get("current_job_id")
    if current_job_id:
        render_results(current_job_id)

    render_cleanup_panel()


if __name__ == "__main__":
    main()
