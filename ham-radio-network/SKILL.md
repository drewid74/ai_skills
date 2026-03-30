---
name: ham-radio-network
description: "Use this skill whenever the user wants to work with ham radio, amateur radio, networking, antenna design, RF calculations, repeater programming, radio frequency planning, or home network infrastructure. Triggers include: any mention of 'ham radio', 'amateur radio', 'HF', 'VHF', 'UHF', 'antenna', 'repeater', 'APRS', 'DMR', 'FT8', 'WSJT', 'SDR', 'software defined radio', 'SWR', 'coax', 'dipole', 'yagi', 'CHIRP', 'Winlink', 'AREDN', 'mesh network', 'AllStar', 'Echolink', 'D-STAR', 'Fusion', 'ICOM', 'Yaesu', 'Kenwood', 'Baofeng', or any callsign pattern. Also use for home network design, VLAN configuration, firewall rules, subnet planning, DNS setup, or any network infrastructure work that involves RF or IP networking for a home lab or ham shack."
---

# Ham Radio & Network Infrastructure Skill

## Overview

Assist with amateur radio operations, antenna design calculations, radio programming, digital modes, and home network infrastructure design and troubleshooting.

## Amateur Radio Calculations

### Antenna Design

**Dipole length**: Total length (feet) = 468 / frequency (MHz)
Each leg = 234 / frequency (MHz)

**Quarter-wave vertical**: Length (feet) = 234 / frequency (MHz)

**Yagi element spacing**: Typically 0.15-0.25 wavelength between elements. Wavelength (feet) = 984 / frequency (MHz)

**Coax loss calculator**: When asked about feedline loss, calculate based on:
- Cable type (RG-58, RG-8X, RG-213, LMR-400, etc.)
- Length in feet
- Frequency
- Use published loss tables per 100ft and scale linearly

**SWR and return loss**:
- Return Loss (dB) = 20 × log10((SWR + 1) / (SWR - 1))
- Mismatch Loss (dB) = 10 × log10(1 - ((SWR - 1)/(SWR + 1))²)
- Power reflected (%) = ((SWR - 1)/(SWR + 1))² × 100

### Link Budget
For estimating signal paths:
- Free Space Path Loss (dB) = 20×log10(d) + 20×log10(f) + 32.44 (d in km, f in MHz)
- Add terrain losses, cable losses, subtract antenna gains

### Repeater Offset Standards (US)
- 2m (144-148 MHz): ±600 kHz
- 70cm (420-450 MHz): ±5 MHz
- 6m (50-54 MHz): ±1 MHz
- 1.25m (222-225 MHz): ±1.6 MHz

## Radio Programming

### CHIRP Support
When generating CHIRP-compatible CSV files for radio programming:

```csv
Location,Name,Frequency,Duplex,Offset,Tone,rToneFreq,cToneFreq,DtcsCode,DtcsPolarity,Mode,TStep,Skip,Comment,URCALL,RPT1CALL,RPT2CALL
0,REPEATER,146.940000,-,0.600000,Tone,100.0,88.5,023,NN,FM,5.00,,Local repeater,,,
```

Key fields:
- **Duplex**: (blank)=simplex, `-`=negative offset, `+`=positive offset, `split`=odd split
- **Tone**: (blank)=none, `Tone`=encode only, `TSQL`=encode+decode, `DTCS`=digital code
- **Mode**: FM, NFM, AM, DV (D-STAR)

### DMR Codeplug Basics
When helping with DMR programming:
- **Talkgroups**: Local (regional), wide (state/national), worldwide
- **Timeslots**: TS1 typically for wide/regional, TS2 for local
- **Color code**: Usually 1, set by repeater
- **Zones**: Group channels by purpose (local, regional, simplex, etc.)

## Digital Modes

### FT8 / WSJT-X Setup
- Audio levels: Keep TX audio just below ALC threshold
- Time sync: Critical — must be within ±1 second (use NTP)
- Frequencies (dial + ~1500 Hz USB):
  - 160m: 1.840 MHz | 80m: 3.573 MHz | 40m: 7.074 MHz
  - 30m: 10.136 MHz | 20m: 14.074 MHz | 17m: 18.100 MHz
  - 15m: 21.074 MHz | 12m: 24.915 MHz | 10m: 28.074 MHz
  - 6m: 50.313 MHz | 2m: 144.174 MHz | 70cm: 432.174 MHz

### APRS
- Standard frequency: 144.390 MHz (North America)
- Path: WIDE1-1,WIDE2-1 (typical)
- Digipeater settings vary by region

### Winlink
- Packet (VHF): 145.010 MHz common
- VARA HF: Various RMS stations, check winlink.org
- Telnet: For testing over internet

## AREDN / Mesh Networking

For ham radio mesh networks:
- Supported hardware: Ubiquiti, Mikrotik, TP-Link (specific models)
- Channels: 900 MHz, 2.4 GHz, 3.4 GHz, 5.8 GHz bands
- Node naming convention: CALLSIGN-location-device
- Tunnel connections for linking distant mesh islands
- Services: VoIP, video, file sharing, chat all running on mesh nodes

## Home Network Infrastructure

### VLAN Design
Recommended VLAN layout for a ham/home lab:

| VLAN | Name | Subnet | Purpose |
|------|------|--------|---------|
| 1 | Management | 10.0.1.0/24 | Switches, APs, IPMI |
| 10 | Trusted | 10.0.10.0/24 | Personal devices |
| 20 | IoT | 10.0.20.0/24 | Smart home, isolated |
| 30 | Ham | 10.0.30.0/24 | Radio computers, SDR servers |
| 40 | Servers | 10.0.40.0/24 | TrueNAS, Docker hosts |
| 50 | Guest | 10.0.50.0/24 | Guest WiFi, isolated |
| 99 | DMZ | 10.0.99.0/24 | Public-facing services |

### Firewall Rules Principles
- Default deny between VLANs
- IoT VLAN: No outbound to LAN, limited internet
- Ham VLAN: Access to servers, no access to trusted
- Servers VLAN: Accept connections from trusted + ham, limited outbound

### DNS Architecture
- Local DNS resolver (Pi-hole, AdGuard Home, or Unbound)
- Split-horizon DNS for internal services
- `.local` or custom domain for internal hostnames
- Forward external queries through DoH/DoT

### Useful Network Calculations
- **Subnet**: Given a CIDR, calculate network, broadcast, usable range, host count
- **IP planning**: Given requirements, suggest appropriate CIDR blocks
- **Bandwidth**: Convert between Mbps, MB/s, and estimate transfer times

## Integration with Other Skills

This skill works well alongside:
- **docker-selfhost**: For containerized radio services (SDR servers, APRS-IS gateways, etc.)
- **github-workflow**: For version-controlling configs and codeplugs

## Output Format

- Antenna calculations: Show the math, provide the result, note practical considerations
- Radio configs: Generate importable files (CHIRP CSV, DMR codeplug templates)
- Network designs: ASCII diagrams or structured tables with all relevant details
- Always include safety notes where applicable (RF exposure, tower work, grounding)
