# HackberryPi CM5 swivel-slide display: design notes (v4)
 
Display: Waveshare 5.5" 1440x2560 LCD (glass 140.40 x 74.76 mm, 8.70 mm deep), mounted on a HackberryPi CM5.
 
## Motion
- Closed: display part sits portrait over the Hackberry, same 91.77 x 143.47 mm footprint.
- Open: rotate 90 degrees about a pivot on the antenna tab, then slide 49 mm left; HDMI edge on top.
- Pivot at (-41.5, 61.4) in the middle-part STL frame; rail tilted 7.3 degrees in the back plate.
## Parts (v3)
1. Middle part with hinge tower, plus lock block left of the antenna tab. The tower holds a captive M2.5 hex nut placed mid-print (pocket z = 12.2 to 14.4 mm, pause at 14.4 mm).
2. Display case: 15 mm deep, glass pocket 140.90 x 75.26 mm, four bosses for M2.5 heat-set inserts (3.2 mm hole, 5 mm deep).
3. Back plate (v4): 4 mm, rail channel open at the ear end, six hold-down posts on the display standoffs, counterbored M2.5 holes. The STL is several overlapping bodies; the slicer must union them (default in most slicers).
4. Hinge slider: M2.5 version, counterbored for a cap or pan head.
5. Lock bolt and knob: vertical bolt in the lock block, pushed up into the back plate to lock closed and open. The bolt goes into the block from the back, tongue first; the knob screw passes through the side slot into the bolt and keeps it captive.
6. Rail gate (v4): a 5.7 x 2.2 mm bar that slides sideways through the ear and closes the rail end. A sprung tooth latches behind the right-hand wall of the opening. Press the tooth and pull the handle to remove it; the display then slides about 30 mm off the slider, which stays on the Hackberry.
## Openings in the case
- HDMI edge: one opening covering headphone jack, HDMI and power (61 mm).
- Short end next to the touch port: 15 mm opening for the touch micro-USB plug.
## Hardware
- Pivot: M2.5 x 8 cap-head screw into a standard M2.5 hex nut (5.0 mm across flats, 2.0 mm thick) captive in the tower. A longer screw would hit the tab lid.
- Case to back plate: 4x M2.5 x 6 screws into M2.5 x 4 heat-set inserts (3.5 mm outer diameter).
- Lock knob: 1x M2.5 x 8 screw, self-tapping into the printed bolt.
## Assumptions to re-check
- Connector and standoff positions were measured from photos, about +/- 1 mm.
- Top cover is 5.0 mm thick and sits on the frame wall top (front face at z = 15.66).
- Open position overlaps the top 2.1 mm of the Hackberry screen opening.
 