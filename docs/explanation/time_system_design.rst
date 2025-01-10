Time System Design
==================

UTMS’s time system is designed to offer high precision while remaining flexible and scalable. The decision to implement a **logarithmic time system** was driven by the desire to handle time at vastly different scales, from Planck time (extremely small) to cosmic time (astronomically large).

Key Concepts
-------------
- **Time Anchors**: Anchors serve as precise reference points in time. By creating anchors at key moments, users can compare and manipulate times relative to these points.
- **Time Units**: UTMS supports multiple time units, including seconds, minutes, hours, and custom units defined by the user.
- **Logarithmic Scale**: Time intervals are represented using a logarithmic scale, allowing for extremely small or large timescales to be handled effectively.
- **Unit Conversions**: UTMS supports conversion between different units, such as converting from seconds to hours or from microseconds to Planck time.

Time in UTMS is handled as a combination of these concepts, which are abstracted into commands like `utms anchor create`, `utms unit convert`, and others.
