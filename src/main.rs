use std::env;
use subprocess::{Popen,PopenConfig};

fn launch_browser(profile_dir: &str, url: Option<&str>) {
    let profile_dir_arg = &format!("--profile-directory={}", profile_dir);
    let mut command: Vec<&str> = vec!["/usr/bin/flatpak","run","--branch=stable","--arch=x86_64","--command=/app/bin/chrome","--file-forwarding","com.google.Chrome", profile_dir_arg];

    if url.is_some() {
        command.push(url.unwrap());
    }

    Popen::create(&command, PopenConfig::default()).expect("Flatpak should be runnable").wait().expect("Chrome should launch cleanly");
}



fn main() {
    let args: Vec<String> = env::args().collect();
    dbg!(args);
    launch_browser("Profile 2", Some("www.github.com"))
}
