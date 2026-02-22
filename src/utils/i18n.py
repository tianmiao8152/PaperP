class Language:
    ENGLISH = 0
    CHINESE = 1

class I18N:
    Language = Language
    current_language = Language.ENGLISH
    
    translations = {
        # App messages
        "app_starting": {Language.ENGLISH: "Application starting...", Language.CHINESE: "正在启动应用..."},
        "app_terminating": {Language.ENGLISH: "Application terminating normally", Language.CHINESE: "应用正常关闭"},
        "paper": {Language.ENGLISH: "PAPER - Pen Adb Password Easily Reset", Language.CHINESE: "PAPER - 一键重置词典笔 ADB 密码"},
        "press_enter_exit": {Language.ENGLISH: "Press Enter to exit...", Language.CHINESE: "按回车键退出..."},
        "unknown_error": {Language.ENGLISH: "An error occurred: {}", Language.CHINESE: "发生错误: {}"},
        
        # IO messages
        "confirm_prefix": {Language.ENGLISH: "[CONFIRM]", Language.CHINESE: "[确认]"},
        "confirm_suffix": {Language.ENGLISH: "[y/N]", Language.CHINESE: "[是(y)/否(N)]"},
        "input_prefix": {Language.ENGLISH: "[INPUT]", Language.CHINESE: "[输入]"},
        "dialog_input_title": {Language.ENGLISH: "Input", Language.CHINESE: "输入"},
        "dialog_confirm_title": {Language.ENGLISH: "Confirm", Language.CHINESE: "确认"},
        "debug_prefix": {Language.ENGLISH: "[DEBUG]", Language.CHINESE: "[调试]"},
        "info_prefix": {Language.ENGLISH: "[INFO]", Language.CHINESE: "[信息]"},
        "warn_prefix": {Language.ENGLISH: "[WARN]", Language.CHINESE: "[警告]"},
        "error_prefix": {Language.ENGLISH: "[ERROR]", Language.CHINESE: "[错误]"},
        "use_chinese": {Language.ENGLISH: "Use Chinese language? / 使用中文界面？", Language.CHINESE: "Use Chinese language? / 使用中文界面？"},
        
        # Admin
        "admin_required": {Language.ENGLISH: "This action requires administrative privileges.", Language.CHINESE: "此操作需要管理员权限。"},
        "relaunch_admin": {Language.ENGLISH: "Relaunching as administrator...", Language.CHINESE: "正在以管理员身份重新启动..."},
        
        # Capture
        "starting_capture": {Language.ENGLISH: "Starting packet capture...", Language.CHINESE: "正在启动抓包..."},
        "waiting_packet": {Language.ENGLISH: "Waiting for update packets... Please check updates on your dictpen", Language.CHINESE: "正在等待更新数据包...请在词典笔上检查更新"},
        "captured_request": {Language.ENGLISH: "Captured update request for product", Language.CHINESE: "已抓取到产品更新请求"},
        "interface_not_found": {Language.ENGLISH: "Interface not found", Language.CHINESE: "未找到网络接口"},
        "capture_failed": {Language.ENGLISH: "Capture failed or aborted.", Language.CHINESE: "抓包失败或已中止。"},
        "captured_post": {Language.ENGLISH: "Captured POST request: {}...", Language.CHINESE: "抓取到 POST 请求: {}..."},
        "no_json_body": {Language.ENGLISH: "No JSON object found in body", Language.CHINESE: "响应体中未找到 JSON 对象"},
        "json_parse_fail": {Language.ENGLISH: "Failed to parse JSON body", Language.CHINESE: "解析 JSON 体失败"},
        "json_extract_error": {Language.ENGLISH: "JSON extraction error: {}", Language.CHINESE: "JSON 提取错误: {}"},
        
        # Download
        "downloading": {Language.ENGLISH: "Downloading firmware...", Language.CHINESE: "正在下载固件..."},
        "downloading_url": {Language.ENGLISH: "Downloading URL: {}", Language.CHINESE: "正在下载 URL: {}"},
        "download_complete": {Language.ENGLISH: "Download completed", Language.CHINESE: "下载完成"},
        "firmware_url": {Language.ENGLISH: "Firmware URL: {}", Language.CHINESE: "固件 URL: {}"},
        "requesting_update": {Language.ENGLISH: "Requesting update info from: {}", Language.CHINESE: "正在请求更新信息: {}"},
        "force_version": {Language.ENGLISH: "Modifying version from {} to 99.99.90 to force full update", Language.CHINESE: "正在将版本从 {} 修改为 99.99.90 以强制获取全量包"},
        "request_body_log": {Language.ENGLISH: "Request body: {}", Language.CHINESE: "请求体: {}"},
        "server_status_error": {Language.ENGLISH: "Server returned status {}: {}", Language.CHINESE: "服务器返回状态码 {}: {}"},
        "update_info_received": {Language.ENGLISH: "Update info received: {}...", Language.CHINESE: "收到更新信息: {}..."},
        "get_update_fail": {Language.ENGLISH: "Failed to get update data: {}", Language.CHINESE: "获取更新数据失败: {}"},
        "file_exists": {Language.ENGLISH: "File {} already exists.", Language.CHINESE: "文件 {} 已存在。"},
        "overwrite_confirm": {Language.ENGLISH: "Overwrite? (y: download again, N: use existing file)", Language.CHINESE: "是否覆盖？(y: 重新下载, N: 使用现有文件)"},
        "using_existing": {Language.ENGLISH: "Using existing file.", Language.CHINESE: "使用现有文件。"},
        "download_progress": {Language.ENGLISH: "Downloading: {:.1f}% ({}/{})", Language.CHINESE: "下载进度: {:.1f}% ({}/{})"},
        "download_fail": {Language.ENGLISH: "Download failed: {}", Language.CHINESE: "下载失败: {}"},
        "json_structure_error": {Language.ENGLISH: "JSON structure mismatch: {}", Language.CHINESE: "JSON 结构不匹配: {}"},
        
        # Patch
        "patching": {Language.ENGLISH: "Patching firmware...", Language.CHINESE: "正在修改固件..."},
        "hash_found": {Language.ENGLISH: "Hash pattern found", Language.CHINESE: "找到哈希模式"},
        "input_password": {Language.ENGLISH: "Please input new password", Language.CHINESE: "请输入新密码"},
        "patch_success": {Language.ENGLISH: "Firmware patched successfully", Language.CHINESE: "固件修改成功"},
        "starting_password_search": {Language.ENGLISH: "Searching for password patterns...", Language.CHINESE: "正在搜索密码模式..."},
        "hash_found_sha256": {Language.ENGLISH: "Hash pattern found (SHA256) at offset {}", Language.CHINESE: "发现哈希模式 (SHA256) 偏移量 {}"},
        "hash_found_md5": {Language.ENGLISH: "Hash pattern found (MD5) at offset {}", Language.CHINESE: "发现哈希模式 (MD5) 偏移量 {}"},
        "error_reading_file": {Language.ENGLISH: "Error reading file: {}", Language.CHINESE: "读取文件错误: {}"},
        "no_passwords_found": {Language.ENGLISH: "No password patterns found.", Language.CHINESE: "未找到密码模式。"},
        "multiple_password_patterns": {Language.ENGLISH: "Multiple password patterns found.", Language.CHINESE: "发现多个密码模式。"},
        "input_new_password": {Language.ENGLISH: "Please input new password", Language.CHINESE: "请输入新密码"},
        "new_hash_log": {Language.ENGLISH: "New Hash: {}", Language.CHINESE: "新哈希值: {}"},
        "patch_fail": {Language.ENGLISH: "Failed to patch file: {}", Language.CHINESE: "修改文件失败: {}"},
        "calculating_hash": {Language.ENGLISH: "Calculating hashes...", Language.CHINESE: "正在计算哈希..."},
        
        # Host/Server
        "hosts_modified": {Language.ENGLISH: "Hosts file modified", Language.CHINESE: "Hosts 文件已修改"},
        "hosts_backup_create": {Language.ENGLISH: "Creating hosts backup", Language.CHINESE: "正在创建 Hosts 备份"},
        "hosts_backup_restore": {Language.ENGLISH: "Restoring hosts file from backup...", Language.CHINESE: "正在从备份恢复 Hosts 文件..."},
        "hosts_restored": {Language.ENGLISH: "Hosts file restored", Language.CHINESE: "Hosts 文件已恢复"},
        "server_start": {Language.ENGLISH: "Server started on port 80", Language.CHINESE: "服务器已在 80 端口启动"},
        "server_stop_hint": {Language.ENGLISH: "Press Ctrl+C to stop", Language.CHINESE: "按 Ctrl+C 停止"},
        "dns_flushed": {Language.ENGLISH: "DNS Cache Flushed", Language.CHINESE: "DNS 缓存已刷新"},
        "dns_flush_fail": {Language.ENGLISH: "Failed to flush DNS cache", Language.CHINESE: "刷新 DNS 缓存失败"},
        "hosts_modify_fail": {Language.ENGLISH: "Failed to modify hosts file: {}", Language.CHINESE: "修改 Hosts 文件失败: {}"},
        "hosts_restore_fail": {Language.ENGLISH: "Failed to restore hosts file: {}", Language.CHINESE: "恢复 Hosts 文件失败: {}"},
        "flask_debug_enabled": {Language.ENGLISH: "Flask debug logging enabled", Language.CHINESE: "Flask 调试日志已启用"},
        "port_occupied": {Language.ENGLISH: "Port {} is already in use or permission denied.", Language.CHINESE: "端口 {} 已被占用或权限不足。"},
        "stop_other_servers": {Language.ENGLISH: "Please stop any other web servers (IIS, Apache, Skype, etc.) running on port 80.", Language.CHINESE: "请停止运行在 80 端口的其他 Web 服务器 (IIS, Apache, Skype 等)。"},
        "check_netstat": {Language.ENGLISH: "You can try running 'netstat -ano | findstr :80' to find the process ID.", Language.CHINESE: "你可以尝试运行 'netstat -ano | findstr :80' 来查找进程 ID。"},
        "server_start_fail": {Language.ENGLISH: "Failed to start server: {}", Language.CHINESE: "启动服务器失败: {}"},
        "retry_port": {Language.ENGLISH: "Press Enter to retry starting the server...", Language.CHINESE: "按回车键重试启动服务器..."},
        "unexpected_error": {Language.ENGLISH: "Unexpected error starting server: {}", Language.CHINESE: "启动服务器时发生意外错误: {}"},
        "ota_check_received": {Language.ENGLISH: "Received OTA check request: {}", Language.CHINESE: "收到 OTA 检查请求: {}"},
        "serving_firmware": {Language.ENGLISH: "Serving firmware: {}", Language.CHINESE: "正在分发固件: {}"},
        "firmware_not_found": {Language.ENGLISH: "Firmware file not found", Language.CHINESE: "固件文件未找到"},
        "server_shutdown_error": {Language.ENGLISH: "Error during server shutdown: {}", Language.CHINESE: "关闭服务器时发生错误: {}"},
        "server_stopped": {Language.ENGLISH: "Server stopped.", Language.CHINESE: "服务器已停止。"},
        "image_request_received": {Language.ENGLISH: "Request for image.img received from {}", Language.CHINESE: "收到来自 {} 的 image.img 请求"},
        "serve_progress_error": {Language.ENGLISH: "Error serving with progress: {}", Language.CHINESE: "分发文件进度显示错误: {}"},
        "complete_prev_step": {Language.ENGLISH: "Please complete the previous step ({}) first.", Language.CHINESE: "请先完成上一步 ({})。"},
        
        # UI Messages
        "window_title": {Language.ENGLISH: "PaperP - DictPen ADB Tool", Language.CHINESE: "PaperP - 词典笔 ADB 工具"},
        "ui_init": {Language.ENGLISH: "PaperP UI Initialized. Ready to start.", Language.CHINESE: "PaperP UI 初始化完成，准备就绪。"},
        "app_title": {Language.ENGLISH: "PaperP", Language.CHINESE: "PaperP"},
        "local_ip_label": {Language.ENGLISH: "Local IP:", Language.CHINESE: "本机 IP:"},
        "log_console_label": {Language.ENGLISH: "Log Console", Language.CHINESE: "日志控制台"},
        "no_capture_result": {Language.ENGLISH: "No capture result found.", Language.CHINESE: "未找到抓包结果。"},
        "starting_capture_ui": {Language.ENGLISH: "Starting Capture...", Language.CHINESE: "正在启动抓包..."},
        "stopping_server": {Language.ENGLISH: "Stopping server...", Language.CHINESE: "正在停止服务器..."},
        "server_stop_success": {Language.ENGLISH: "Server stopped successfully.", Language.CHINESE: "服务器已成功停止。"},
        "step_error": {Language.ENGLISH: "Error in step {}: {}", Language.CHINESE: "步骤 {} 发生错误: {}"},
        "lang_switch_log": {Language.ENGLISH: "Language switched to {}", Language.CHINESE: "语言切换为 {}"},
        
        # UI Steps
        "step_capture": {Language.ENGLISH: "1. Capture Request", Language.CHINESE: "1. 抓取请求"},
        "step_download_info": {Language.ENGLISH: "2. Get Update Info", Language.CHINESE: "2. 获取更新信息"},
        "step_download_file": {Language.ENGLISH: "3. Download Firmware", Language.CHINESE: "3. 下载固件"},
        "step_patch": {Language.ENGLISH: "4. Patch Firmware", Language.CHINESE: "4. 修改固件"},
        "step_network": {Language.ENGLISH: "5. Host Redirect", Language.CHINESE: "5. Hosts 重定向"},
        "step_server": {Language.ENGLISH: "6. Start Server", Language.CHINESE: "6. 启动服务器"},
        
        "language_switch_btn": {Language.ENGLISH: "中文 / EN", Language.CHINESE: "English / 中文"},
        "lang_chinese": {Language.ENGLISH: "Chinese", Language.CHINESE: "中文"},
        "lang_english": {Language.ENGLISH: "English", Language.CHINESE: "英文"},
        
        # Argparse
        "ui_load_fail": {Language.ENGLISH: "Failed to load UI: {}", Language.CHINESE: "加载 UI 失败: {}"},
        "ui_start_error": {Language.ENGLISH: "Error starting UI: {}", Language.CHINESE: "启动 UI 失败: {}"},
        "fallback_cli": {Language.ENGLISH: "Falling back to CLI mode.", Language.CHINESE: "回退到命令行模式。"},
        "server_restart_hint": {Language.ENGLISH: "Server failed to start, attempting to restart...", Language.CHINESE: "服务器启动失败，正在尝试重启..."},
        
        # Shortcuts
        "restore_hosts_btn": {Language.ENGLISH: "Restore Hosts", Language.CHINESE: "还原 hosts"},
        "force_stop_service_btn": {Language.ENGLISH: "Force Stop Service", Language.CHINESE: "强行停止服务"},
        "no_process_on_port_80": {Language.ENGLISH: "No process found on port 80", Language.CHINESE: "80 端口未发现占用进程"},
        "killing_process": {Language.ENGLISH: "Killing process {}...", Language.CHINESE: "正在结束进程 {}..."},
        "port_80_cleared": {Language.ENGLISH: "Port 80 process cleared", Language.CHINESE: "80 端口进程已清理"},
        "force_stop_fail": {Language.ENGLISH: "Failed to force stop service: {}", Language.CHINESE: "强制停止服务失败: {}"},
    }

    @staticmethod
    def t(key):
        if key not in I18N.translations:
            return key
        return I18N.translations[key].get(I18N.current_language, key)

    @staticmethod
    def set_language(lang):
        I18N.current_language = lang

def t(key):
    return I18N.t(key)
