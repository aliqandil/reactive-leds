# reactive-leds
This project aims to provide a rather new look at RGB keyboards, not just as aesthetics but also as a helper utility that can provide a visual feedback of the state of your machine. It can also act as a last resort when there might be display problems!

## Supported Devices
This is mostly a personal project, that I use to control my laptop's LEDs, which is a `Lenovo Legion7` with the model number `16ITHG6`.
So currently this repository is probably not going to work on any other devices, including most other models of Lenovo Legion7s, maybe it'll also work on `16ACH6H`.
And also, I'm using this code on a `Manjaro Linux`, So It might have problems on other linux versions, and it most definitley won't run on `Windows`, Since I believe windows doesn't support `Duplex Pipes` which I've used to decouple the usercode with the `HIDInterface` so a laggy code doens't effect the performance and refresh rate of the leds.

I don't really have the time or care enough to make this code work on every single device, and on every OS,
but at the very least I want it to work on all `Legion 7` Keyboards, preferably also on Windows.

## What it does [Or Just Watch This](https://github.com/aliqandil/reactive-leds/raw/main/reactive-leds-demo.mp4)  
Currently, the `reactive_leds` python package, is enough to do almost anything you want with your LEDs including the NEON and VENTS and the LOGO.
There is also an `actions` directory, which is run in order by the `startservice.py` file.
Check them out for some examples.

I also use it as a restart button when the graphics card on my laptop glitches out, by holding both Ctrl buttons for 10 seconds. (not included in this repository)

## Prerequisites
[pyhidapi](https://github.com/apmorton/pyhidapi) Package. Don't forget to read the installation steps for `hidapi`.
### Security Note
Any code that has acces to HID devices, is capable of a great deal of actions, including listening in on all keystrokes!
So this code should either be run as root (probably a service) or be granted access to interface with HID devices.
If you choose to use a custom animation (action) someone else may provide, be sure to read it thoroughly!

[Colour](https://github.com/vaab/colour) Package.
`reactive_leds` module itself does not depend on this, but can work with it.
The examples in the `actions` directory does depend on `Colour` though.




## Contributions
Issues and Ideas are appreciated.
Since I feel like the utilities of a good LED keyboard are generaly under-rated,
I'd like to hear your ideas on what can be done with this.


### Note
This project isn't a priority for me, so I might be slow to develope and answer issues.
I do have access to two other legion7s (`15IMH05` and `15IMH5`) So those two will probably be the first ones to work with this code.
This whole project was the outcome of this [OpenRGB issue](https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues/1635).
Reading it might give you some ideas how it works. There is also a [snippet I've posted there](https://gitlab.com/-/snippets/2230241),
which is a much smaller but less efficient version of this repo, that encapsulates some of the core ideas of this project.
