
import flet as ft
import requests
import os
import pathlib
from murf import Murf
try:
    from api_key import API_KEY
except ImportError:
    API_KEY = "" # Để trống nếu không tìm thấy file

client = None 
def initialize_murf_client(api_key):
    global client
    if not api_key:
        print("API Key trống, không thể khởi tạo Murf client.")
        client = None
        return False, "API Key trống."
    try:
        print(f"Đang thử khởi tạo Murf client với key: ...{api_key[-4:]}") # Chỉ log 4 ký tự cuối để đối chiếu đúng API
        client = Murf(api_key=api_key)
        print("Khởi tạo Murf client thành công.")
        return True, "Khởi tạo thành công."
    except Exception as e:
        print(f"Lỗi khi khởi tạo Murf Client: {e}")
        client = None
        return False, f"Lỗi API: {e}"

initialize_murf_client(API_KEY)

  
# --- TỰ ĐỘNG LẤY VÀ LỌC VOICE TIẾNG ANH ---
VOICE_MOODS = {} 

if client: 
    try:
        voices = client.text_to_speech.get_voices()
        count_en = 0
        for voice in voices:
            # Kiểm tra xem voice_id có bắt đầu bằng 'en-' không (không phân biệt hoa thường)
            if voice.voice_id and (voice.voice_id.lower().startswith("en-us-") or voice.voice_id.lower().startswith("en-uk-")):
                display_name = voice.display_name 
                voice_id = voice.voice_id
                moods = voice.available_styles if isinstance(voice.available_styles, list) else []
                if not moods:
                    moods = ['default'] 

                VOICE_MOODS[display_name] = {
                    "voice_id": voice_id,
                    "moods": moods
                }
                count_en += 1

        VOICE_MOODS = dict(sorted(VOICE_MOODS.items()))

    except Exception as e:
        print(f"Lỗi khi lấy hoặc xử lý voices từ Murf API: {e}")
        print("Sử dụng danh sách voices mặc định hoặc để trống.")
else:
    print("Client Murf chưa được khởi tạo. Không thể lấy danh sách voices.")
    # Đảm bảo VOICE_MOODS rỗng trong trường hợp này
    VOICE_MOODS = {}

# Kiểm tra cuối cùng xem có voice nào không
if not VOICE_MOODS:
     print("CẢNH BÁO: Không có voice nào được tải vào VOICE_MOODS.")

# Build the Flet App
def main(page: ft.Page):
    page.title = "AI Voice Generator-Nguyen Giap High School"
    page.window_icon = "assets/icon.png"
    page.vertical_alignment = ft.MainAxisAlignment.START # Đổi thành Start để nút cài đặt ở trên
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = ft.padding.symmetric(horizontal=40, vertical=20) # Điều chỉnh padding
    page.bgcolor = "#1E1E2F"

    _audio_url_to_save = None

    def save_file_result(e: ft.FilePickerResultEvent):
        nonlocal _audio_url_to_save 
        if not e.path:
            print("Người dùng đã hủy việc lưu file.")
            page.snack_bar = ft.SnackBar(content=ft.Text("Đã hủy lưu file."))
            page.snack_bar.open = True
            _audio_url_to_save = None 
            page.update() 
            return

        if not _audio_url_to_save:
            print("Lỗi: Không có URL audio để lưu.")
            page.snack_bar = ft.SnackBar(content=ft.Text("Lỗi nội bộ: Không tìm thấy URL audio."), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return

        save_path_str = e.path
        if not save_path_str.lower().endswith(".mp3"):
            save_path_str += ".mp3"

        save_path = pathlib.Path(save_path_str)
        print(f"Đang lưu file vào: {save_path}")
        page.snack_bar = ft.SnackBar(content=ft.Text(f"Đang lưu vào {save_path.name}..."))
        page.snack_bar.open = True
        page.update() 

        try:
            response = requests.get(_audio_url_to_save, stream=True, timeout=60) 
            response.raise_for_status() 

            with open(save_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

            print("Audio Saved As:", save_path)
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Đã lưu thành công vào {save_path.name}!"), bgcolor=ft.colors.GREEN)
            page.snack_bar.open = True


            current_audio = next((ctl for ctl in page.overlay if isinstance(ctl, ft.Audio)), None)
            if current_audio:
                page.overlay.remove(current_audio)

            audio_src = save_path.resolve().as_uri()
            print(f"Playing audio from: {audio_src}")
            page.overlay.append(ft.Audio(src=audio_src, autoplay=True))
            page.update()

        except requests.exceptions.Timeout:
            error_msg = "Lỗi: Hết thời gian chờ khi tải audio."
            print(error_msg)
            page.snack_bar = ft.SnackBar(content=ft.Text(error_msg), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
        except requests.exceptions.RequestException as req_e:
            error_msg = f"Lỗi mạng khi tải audio: {req_e}"
            print(error_msg)
            page.snack_bar = ft.SnackBar(content=ft.Text(error_msg), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
        except IOError as io_e:
            error_msg = f"Lỗi I/O khi lưu file: {io_e}"
            print(error_msg)
            page.snack_bar = ft.SnackBar(content=ft.Text(error_msg), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            error_msg = f"Lỗi không xác định khi lưu/phát: {ex}"
            print(error_msg)
            page.snack_bar = ft.SnackBar(content=ft.Text(error_msg), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
        finally:
             _audio_url_to_save = None

    file_picker = ft.FilePicker(on_result=save_file_result)
    if file_picker not in page.overlay:
         page.overlay.append(file_picker)

    title = ft.Text(
    spans=[
        ft.TextSpan(
            "Made with ",
            ft.TextStyle(
                size=36, 
                weight=ft.FontWeight.BOLD, 
                color="#FFD700", 
            ),
        ),
        ft.TextSpan(
            "❤️", 
            ft.TextStyle(
                size=36, 
                weight=ft.FontWeight.BOLD, 
                color=ft.colors.RED,
            ),
        ),
        ft.TextSpan(
            " for Lê Thảo Hiền",
            ft.TextStyle(
                size=36, 
                weight=ft.FontWeight.BOLD, 
                color="#FFD700",
            ),
        ),
    ],
    text_align=ft.TextAlign.CENTER 
    )
    # Hiển thị trạng thái API Key hiện tại
    api_status_text = ft.Text(
        f"API Key: {'Đã thiết lập' if client else 'Chưa thiết lập'}",
        color=ft.colors.GREEN if client else ft.colors.RED,
        italic=True,
        size=12
    )

    api_key_input_dialog = ft.TextField(
        label="Nhập API Key Murf.ai mới",
        password=True,
        can_reveal_password=True,
        bgcolor="#3e3e4f", 
        color="#ffffff",
        border_color="#FFD700",
        border_radius=10
    )

    def update_api_key(e):
        new_key = api_key_input_dialog.value.strip()
        if not new_key:
            page.snack_bar = ft.SnackBar(content=ft.Text("API Key không được để trống!"), bgcolor=ft.colors.ORANGE)
            page.snack_bar.open = True
            page.update()
            return

        success, message = initialize_murf_client(new_key)

        if success:
            page.snack_bar = ft.SnackBar(content=ft.Text("API Key đã được cập nhật thành công!"), bgcolor=ft.colors.GREEN)
            api_status_text.value = "API Key: Đã thiết lập"
            api_status_text.color = ft.colors.GREEN
            global API_KEY
            API_KEY = new_key
            # Ghi vào file api_key.py cho lần sau
            try:
                with open("api_key.py", "w") as f:
                    f.write(f'API_KEY = "{new_key}"\n')
            except IOError as io_err:
                print(f"Không thể lưu API Key vào file: {io_err}")
        else:
            page.snack_bar = ft.SnackBar(content=ft.Text(f"Lỗi cập nhật API Key: {message}"), bgcolor=ft.colors.RED)
            api_status_text.value = "API Key: Lỗi thiết lập"
            api_status_text.color = ft.colors.RED

        page.snack_bar.open = True
        page.close(api_key_dialog)
        page.update()

    def close_dialog(e):
        page.close(api_key_dialog)
        page.update()

    api_key_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Cập nhật API Key", weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                api_key_input_dialog,
                ft.Text("Lấy API Key từ tài khoản Murf.ai của bạn.", size=12, italic=True, color=ft.colors.GREY_500)
            ], tight=True, spacing=10
        ),
        actions=[
            ft.TextButton("Lưu", on_click=update_api_key, style=ft.ButtonStyle(color=ft.colors.GREEN)),
            ft.TextButton("Hủy", on_click=close_dialog, style=ft.ButtonStyle(color=ft.colors.RED)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor="#2A2A3B",
        shape=ft.RoundedRectangleBorder(radius=15)
    )

    def open_api_key_dialog(e):
        api_key_input_dialog.value = "" # Xóa giá trị cũ trước khi mở
        page.open(api_key_dialog) # Mở dialog
        page.update()

    settings_button = ft.IconButton(
        ft.icons.SETTINGS_OUTLINED,
        tooltip="Thay đổi API Key",
        icon_color="#FFD700",
        on_click=open_api_key_dialog
    )

    text_input = ft.TextField(
        label="Nhập đoạn văn bản của bạn ở đây...",
        width=350,
        bgcolor="#2A2A3B",
        color="#ffffff",
        border_radius=15,
        border_color="#FFD700",
        multiline=True,
        min_lines=3,
        max_lines=4,
        shift_enter=False
    )
    voice_selection = ft.Dropdown( 
        label="Choose Voice",
        options=[ft.dropdown.Option(voice) for voice in VOICE_MOODS.keys()],
        width=350,
        bgcolor="#ffffff",
        border_color="#FFD700",
        color="#ffffff",
        value="Miles"
    )
    mood_selection = ft.Dropdown( 
        label="Choose Mood",
        width=350,
        bgcolor="#ffffff",
        border_color="#FFD700",
        color="#ffffff",
    )
    def update_moods(e=None): 
        selected_voice = voice_selection.value
        available_moods = VOICE_MOODS.get(selected_voice, {}).get("moods", [])
        mood_selection.options = [ft.dropdown.Option(mood) for mood in available_moods]
        mood_selection.value = available_moods[0] if available_moods else None
        page.update() 
    voice_selection.on_change = update_moods
    update_moods()

    voice_speed = ft.Slider( 
        min=-30, max=30, value=0, divisions=12, label="{value}% Pitch",
        active_color="#FFD700", inactive_color="#44445a"
    )
    progress_ring = ft.ProgressRing(visible=False, width=20, height=20, stroke_width=3)
    status_text = ft.Text("", color="#FFD700", size=12)

    def generate_audio():
        if client is None:
            print("Lỗi: Murf client chưa được khởi tạo hoặc API Key không hợp lệ.")
            page.snack_bar = ft.SnackBar(content=ft.Text("Lỗi: API Key chưa được thiết lập hoặc không hợp lệ. Vui lòng kiểm tra cài đặt."), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return None 

        progress_ring.visible = True
        status_text.value = "Đang tạo audio..."
        btn_enter.disabled = True
        page.update()

        selected_voice = voice_selection.value
        voice_id = VOICE_MOODS.get(selected_voice,{}).get("voice_id")
        text = text_input.value.strip()
        selected_mood = mood_selection.value
        pitch_value = int(voice_speed.value)

        audio_url = None

        if not text:
            print("ERROR, you need some text...")
            page.snack_bar = ft.SnackBar(content=ft.Text("Vui lòng nhập nội dung text!"), bgcolor=ft.colors.ORANGE)
            page.snack_bar.open = True
        elif not selected_mood:
             print("ERROR, you need to select a mood...")
             page.snack_bar = ft.SnackBar(content=ft.Text("Vui lòng chọn một mood!"), bgcolor=ft.colors.ORANGE)
             page.snack_bar.open = True
        elif not voice_id:
             print("ERROR, voice ID not found...")
             page.snack_bar = ft.SnackBar(content=ft.Text("Lỗi: Không tìm thấy Voice ID."), bgcolor=ft.colors.RED)
             page.snack_bar.open = True
        else:
            print(f"Generating audio with Voice: {selected_voice}, Mood: {selected_mood}, Pitch: {pitch_value}")
            try:
                response = client.text_to_speech.generate(
                    format="MP3",
                    sample_rate=48000,
                    channel_type="STEREO",
                    text=text,
                    voice_id=voice_id,
                    style=selected_mood,
                    pitch=pitch_value
                )
                print("API Response received.")
                if hasattr(response, "audio_file") and response.audio_file:
                    print(f"Audio URL: {response.audio_file}")
                    audio_url = response.audio_file
                    status_text.value = "Tạo audio thành công!"
                else:
                    error_detail = getattr(response, 'message', 'Không có audio_file trả về.')
                    print(f"Lỗi từ API Murf hoặc không tìm thấy audio_file: {error_detail}")
                    page.snack_bar = ft.SnackBar(content=ft.Text(f"Lỗi API: {error_detail}"), bgcolor=ft.colors.RED)
                    page.snack_bar.open = True

            except Exception as e:
                error_msg = f"Lỗi khi gọi API Murf: {e}"
                print(error_msg)
                page.snack_bar = ft.SnackBar(content=ft.Text(error_msg), bgcolor=ft.colors.RED)
                page.snack_bar.open = True

        progress_ring.visible = False
        btn_enter.disabled = False
        page.update()
        return audio_url


    def generate_and_show_save_dialog(e):
        nonlocal _audio_url_to_save
        audio_url = generate_audio()
        if audio_url:
            _audio_url_to_save = audio_url
            print("Đã nhận URL audio, đang mở hộp thoại lưu file...")
            status_text.value = "Vui lòng chọn nơi lưu file..."
            page.update()
            file_picker.save_file(
                dialog_title="Lưu file âm thanh",
                file_name="generated_audio.mp3",
                allowed_extensions=["mp3"]
            )
        else:
            print("Không tạo được audio URL, không thể mở hộp thoại lưu.")
            status_text.value = "Tạo audio thất bại."
            page.update()


    btn_enter = ft.ElevatedButton(
        "Tạo và Lưu Âm thanh",
        bgcolor="#FFD700",
        color="#1E1E2F",
        on_click=generate_and_show_save_dialog,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
        height=50
    )

    input_container = ft.Container(
        content=ft.Column(
            [
                text_input,
                voice_selection,
                mood_selection,
                ft.Text("Chỉnh sửa Pitch", size=18, weight=ft.FontWeight.BOLD, color="#FFD700"),
                voice_speed,
                ft.Row(
                    [btn_enter, progress_ring, status_text],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                )
            ],
            spacing=15,
        ),
        padding=20,
        border_radius=20,
        bgcolor="#2A2A3B",
        shadow=ft.BoxShadow(blur_radius=12, spread_radius=2, color=ft.colors.with_opacity(0.5, "#FFD700"))
    )

    page.add(
        ft.Row(
            [title, ft.Container(expand=True), settings_button],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),

        ft.Column(
            controls=[
                api_status_text,
                ft.Divider(
                    height=10, color=ft.colors.with_opacity(0.5, "#FFD700")),
                input_container,
            ],
            expand=True,           
            scroll=ft.ScrollMode.AUTO  
        )
    )
    page.update()

# Run the App
if __name__ == "__main__":
    ft.app(target=main, assets_dir=".")