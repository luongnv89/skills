import 'package:flutter/material.dart';

import '../game/content.dart';

/// A dive: the lantern fish, an oxygen bar top left, the creature log top right,
/// and the flash button bottom right. Drag anywhere to swim.
class DiveScreen extends StatefulWidget {
  const DiveScreen({super.key, required this.reef});
  final Reef reef;

  @override
  State<DiveScreen> createState() => _DiveScreenState();
}

class _DiveScreenState extends State<DiveScreen> {
  late int oxygen = widget.reef.oxygen;
  final log = <String>[];

  void touch(String creature) => setState(() {
        if (creature == 'stingray') {
          oxygen -= stingrayOxygenCost; // stings: never collected
        } else if (collectible.contains(creature)) {
          log.add(creature);
        }
      });

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: const Color(0xFF06121F),
        body: SafeArea(
          child: Stack(children: [
            Positioned(
              left: 16, top: 12,
              child: Row(children: [
                const Icon(Icons.bubble_chart, color: Color(0xFF59D2FE)),
                Text(' OXYGEN $oxygen s', style: const TextStyle(color: Color(0xFF59D2FE), fontSize: 16)),
              ]),
            ),
            Positioned(
              right: 16, top: 12,
              child: Text('LOG ${log.length}/${collectible.length}',
                  style: const TextStyle(color: Color(0xFFFFC857), fontSize: 16)),
            ),
            Center(child: Text(widget.reef.name, style: const TextStyle(color: Color(0x33E6F1FF), fontSize: 48))),
            const Positioned(
              right: 24, bottom: 24,
              child: CircleAvatar(radius: 32, backgroundColor: Color(0xFFFFC857), child: Icon(Icons.flare, color: Color(0xFF06121F))),
            ),
          ]),
        ),
      );
}
