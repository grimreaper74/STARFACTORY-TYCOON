# Development Build R30 — Keyboard Route

Build root: `E:\LineBossValidationOutput\Builds\Development_20260821_factory_r30_keyboard\Windows`

## Purpose

R30 is the current playable development build. It supersedes R29 for keyboard
testing after a player reported that mouse controls worked while keyboard
shortcuts did not.

`ALBOneFactoryPlayerController` now intercepts supported pressed keys in its
controller-level `InputKey` override before ordinary PlayerInput dispatch. This
keeps factory controls reachable when a native UMG control owns Slate focus
after a mouse click. Existing direct key bindings and widget preview forwarding
remain in place as compatible paths.

## Player shortcuts

| Key | Action |
| --- | --- |
| `N` or `B` | Start the next compatible vehicle order |
| `Space` | Pause or resume the factory line |
| `1`, `2`, `3` | Run at 1×, 2×, or 4× |
| `F1`–`F4` | Focus Press, Body, Paint, or Assembly |
| `Q`, `R`, `M` | Resolve hold, rework hold, or service plant |

## Validation

- `LineBossCarFactoryEditor Win64 Development` compiled successfully.
- Focused automation test
  `LineBoss.OneFactory.ActualPlayer.PauseKeyDrivesDurableLedgerPause` passed.
  It exercises controller shortcut handling for `2` and `Space`, and verifies
  durable pause/resume state and retained 2× speed.
- `BuildCookRun` for Development completed successfully and the completed
  staged build was copied to the build root above.

This is a development validation build. Player runtime confirmation on a normal
mouse-and-keyboard session remains required before calling keyboard support
complete.
