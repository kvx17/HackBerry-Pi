# Hackberry Pi CM5 - Collection of files, scripts, and 3d files

Custom key-layer configuration and the **kvxducky** typing-script loader for the Zitaotech [Hackberry Pi CM5](https://github.com/ZitaoTech/HackberryPiCM5/tree/main).

See  
[3D Files](/3D%20Files/3D.md)  
[Battery](/Battery/Battery.md)  
[Keyboard](/Keyboard/Keyboard.md)  
[kvxducky scripts and the panel](/Keyboard/script-replay/README.md)

**OS**:
- [Parrot OS](/OS/Parrot%20OS/ParrotOS.md)

Other relevant repositories:

- https://github.com/ZitaoTech/HackberryPiCM5
- https://github.com/CNflysky/hackberrypiq20/tree/main

## kvxducky

kvxducky keeps one typing script on the keyboard's RP2040. The CM5 loads that script while the left switch is **internal**. Flipping the switch to **external** and plugging the bottom USB-C into another computer presents the same controller as a USB keyboard (`4242:0003`). Plugging the cable in does not type anything. Hold **Script play** (Vial label **Play**, layer 2, **R**) for about 400 ms to start. Press it again to stop.

The host tool is `Keyboard/script-replay/kvxkeyinject`. It does not run the script on the Pi. It turns the text file into keystrokes and writes those keystrokes into the controller. A line it cannot encode is reported as `error:` and is not stored.

Full instructions, the panel keys, the script language, and the sample files are in [Keyboard/script-replay/README.md](/Keyboard/script-replay/README.md). Flashing, the play key, and recovery are in [Keyboard/Keyboard.md](/Keyboard/Keyboard.md).

Do these in order, from the repo root unless a step says otherwise.

1. Flash the keyboard controller. Left switch **internal**.

   ```bash
   python3 Keyboard/firmware/flash.py
   ```

   Choose **1**. That builds `kvxducky.uf2` when needed and copies it onto the `RPI-RP2` drive. The CM5's SD card and NVMe are not written.

2. In Vial, **File → Load saved layout**, and choose `Keyboard/script_play.vil`. That puts **Script play** on layer 2, **R**. You can assign **Play** to another key yourself.

3. Start the loader once and confirm any missing pieces it offers to install.

   ```bash
   cd Keyboard/script-replay
   python3 kvxkeyinject
   ```

4. Highlight a `.txt` file and press Enter to send it. The left switch stays **internal** while you send. Sample scripts live in `Keyboard/script-replay/examples/`. Your own files go in `Keyboard/script-replay/scripts/`. Press `f` to add another folder; it stays in the list under `scripts`.

5. Flip the left switch to **external**, plug the bottom USB-C into the other computer, and hold **Script play** for about 400 ms.

Hold **Script play** only after the switch is external. With the switch still internal, the script types into the Hackberry.
