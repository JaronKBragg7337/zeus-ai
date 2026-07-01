use std::{
    process::Command as StdCommand,
    sync::{Arc, Mutex},
};

use tauri::{Emitter, WindowEvent};
use tauri_plugin_shell::{
    process::{CommandChild, CommandEvent},
    ShellExt,
};

#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x0800_0000;

fn terminate_backend(child: CommandChild) {
    let pid = child.pid();

    #[cfg(windows)]
    {
        let pid_arg = pid.to_string();
        let _ = StdCommand::new("taskkill")
            .args(["/PID", pid_arg.as_str(), "/T", "/F"])
            .creation_flags(CREATE_NO_WINDOW)
            .status();
    }

    let _ = child.kill();
}

fn main() {
    let backend_child: Arc<Mutex<Option<CommandChild>>> = Arc::new(Mutex::new(None));
    let setup_child = Arc::clone(&backend_child);
    let close_child = Arc::clone(&backend_child);

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(move |app| {
            let app_handle = app.handle().clone();
            let sidecar = app
                .shell()
                .sidecar("zeus-backend")?
                .env("ZEUSAI_DESKTOP", "1")
                .env("ZEUSAI_FULL_COMPUTER_ACCESS", "1")
                .env("ZEUSAI_COMMAND_RISK_POLICY", "log")
                .env("ZEUSAI_BACKEND_HOST", "127.0.0.1")
                .env("ZEUSAI_BACKEND_PORT", "8000");
            let (mut rx, child) = sidecar.spawn()?;

            *setup_child.lock().expect("backend child lock poisoned") = Some(child);

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(bytes) => {
                            println!(
                                "[zeus-backend] {}",
                                String::from_utf8_lossy(&bytes).trim_end()
                            );
                        }
                        CommandEvent::Stderr(bytes) => {
                            eprintln!(
                                "[zeus-backend] {}",
                                String::from_utf8_lossy(&bytes).trim_end()
                            );
                        }
                        CommandEvent::Terminated(payload) => {
                            println!("[zeus-backend] terminated: {:?}", payload);
                            let _ = app_handle.emit("zeus-backend-exited", ());
                        }
                        _ => {}
                    }
                }
            });

            Ok(())
        })
        .on_window_event(move |_window, event| {
            if let WindowEvent::CloseRequested { .. } = event {
                if let Ok(mut guard) = close_child.lock() {
                    if let Some(child) = guard.take() {
                        terminate_backend(child);
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Zeus AI desktop app");
}
