// packages/ui/src/atmosphere.rs

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Atmosphere {
    Arcane,
    Zen,
}

pub struct State {
    pub current_mode: Atmosphere,
}

impl State {
    pub fn new() -> Self {
        Self {
            current_mode: Atmosphere::Zen,
        }
    }

    pub fn switch_to(&mut self, mode: Atmosphere) {
        self.current_mode = mode;
    }
}
