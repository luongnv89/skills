import 'package:flutter/material.dart';

import '../game/content.dart';
import '../store/shop.dart';
import 'dive_screen.dart';

/// The reef map: three seas side by side, a lock and "Deep Pass" on paid seas.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key, required this.shop});
  final Shop shop;

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Column(children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('LANTERN REEF', style: TextStyle(fontSize: 28, color: Color(0xFFFFC857), letterSpacing: 4)),
            ),
            Expanded(
              child: Row(children: [
                for (final sea in seas)
                  Expanded(
                    child: Card(
                      color: const Color(0xFF0B2236),
                      child: Column(children: [
                        Text(sea.name, style: const TextStyle(fontSize: 20, color: Color(0xFFE6F1FF))),
                        if (!shop.unlocked(sea.free))
                          const ListTile(
                            leading: Icon(Icons.lock, color: Color(0xFF7FA3C4)),
                            title: Text('Deep Pass', style: TextStyle(color: Color(0xFF7FA3C4))),
                          ),
                        for (final reef in sea.reefs)
                          ListTile(
                            title: Text('${reef.code} · ${reef.name}', style: const TextStyle(color: Color(0xFFE6F1FF))),
                            enabled: shop.unlocked(sea.free),
                            onTap: () => Navigator.push(context,
                                MaterialPageRoute(builder: (_) => DiveScreen(reef: reef))),
                          ),
                      ]),
                    ),
                  ),
              ]),
            ),
          ]),
        ),
      );
}
