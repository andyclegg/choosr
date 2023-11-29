use std::env;
use subprocess::Popen;

fn launch_browser(profile_dir: &str, url: Option<&str>) {
    let command: Vec<String> = vec!["/usr/bin/flatpak".to_string(),"run".to_string(),"--branch=stable".to_string(),"--arch=x86_64".to_string(),"--command=/app/bin/chrome".to_string(),"--file-forwarding".to_string(),"com.google.Chrome".to_string(),format!("--profile-directory={}", profile_dir)];

    if url.is_some() {
        command.push(url);
    }
}



fn main() {
    let args: Vec<String> = env::args().collect();
    dbg!(args);
    launch_browser("Default", Some("www.github.com"))
}
