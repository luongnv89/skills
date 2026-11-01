/// Seas and reefs. The Shallows are free; Deep Pass (shop.dart) opens the rest.
class Reef {
  const Reef(this.code, this.name, {required this.oxygen});
  final String code;
  final String name;
  final int oxygen; // seconds of oxygen at the start of the dive
}

class Sea {
  const Sea(this.name, this.reefs, {required this.free});
  final String name;
  final List<Reef> reefs;
  final bool free;
}

const seas = [
  Sea('The Shallows', [
    Reef('1-1', 'Kelp Gate', oxygen: 90),
    Reef('1-2', 'Coral Steps', oxygen: 90),
    Reef('1-3', 'Sunken Bell', oxygen: 100),
  ], free: true),
  Sea('Twilight Sea', [
    Reef('2-1', 'Glass Garden', oxygen: 120),
    Reef('2-2', 'Eel Hollow', oxygen: 130),
    Reef('2-3', 'Lantern Arch', oxygen: 140),
  ], free: false),
  Sea('Midnight Sea', [
    Reef('3-1', 'Black Trench', oxygen: 150),
    Reef('3-2', 'Whale Fall', oxygen: 170),
    Reef('3-3', 'The Deep Light', oxygen: 200),
  ], free: false),
];

/// Creatures a touch adds to the log. Stingrays are not in this list: touching
/// one costs 10 s of oxygen and is never collected (see dive_screen.dart).
const collectible = ['glowworm', 'moon jelly', 'lantern shrimp', 'star snail', 'ghost crab'];
const stingrayOxygenCost = 10;
