use dioxus::prelude::*;
use api::{echo, get_mantra_atmosphere};

const ECHO_CSS: Asset = asset!("/assets/styling/echo.css");

#[component]
pub fn Echo() -> Element {
    let mut response = use_signal(|| String::new());
    
    let _mantra_data = use_resource(move || async move {
        get_mantra_atmosphere("some_gesture_data".to_string()).await
    });

    rsx! {
        document::Link { rel: "stylesheet", href: ECHO_CSS }
        div {
            id: "echo",
            h4 { "ServerFn Echo" }
            input {
                placeholder: "Type here to echo...",
                oninput: move |event| {
                    let val = event.value();
                    spawn(async move {
                        if let Ok(data) = echo(val).await {
                            response.set(data);
                        }
                    });
                },
            }

            if !response().is_empty() {
                p {
                    "Server echoed: "
                    i { "{response}" }
                }
            }
        }
    }
}