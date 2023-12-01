use std::{
    env,
    fs::File,
    io::{prelude::*, BufReader},
    path::Path,
};
use subprocess::{Popen,PopenConfig};

fn launch_browser(profile_dir: &str, url: Option<String>) {
    let profile_dir_arg = &format!("--profile-directory={}", profile_dir);
    let mut command: Vec<&str> = vec!["/usr/bin/flatpak","run","--branch=stable","--arch=x86_64","--command=/app/bin/chrome","--file-forwarding","com.google.Chrome", profile_dir_arg];

    let unwrapped_url;
    if url.is_some() {
        unwrapped_url =url.unwrap();
        command.push(&unwrapped_url);
    }

    Popen::create(&command, PopenConfig::default()).expect("Flatpak should be runnable").wait().expect("Chrome should launch cleanly");
}

fn load_domains(filename: impl AsRef<Path>) -> Vec<String> {
    let file = File::open(filename).expect("Domain file not found");
    let buf = BufReader::new(file);
    buf.lines().map(|l| l.expect("Could not parse line")).collect()
}



fn main() {
    let args: Vec<String> = env::args().collect();
    let url = match args.len() {
        1 => None,
        2 => Some(&args[1]),
        _ => panic!("bad number of args")
    };
    let domains = load_domains("work.txt");
    println!("{domains:?}");
    let profile_dir = if (url.is_some() & domains.contains(url.unwrap())) {"Profile 2"} else {"Default"};
    launch_browser(profile_dir, url.cloned())
}
