import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'store/shop.dart';
import 'ui/home_screen.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.landscapeLeft, DeviceOrientation.landscapeRight]);
  await SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
  runApp(LanternReefApp(shop: await Shop.load()));
}

class LanternReefApp extends StatelessWidget {
  const LanternReefApp({super.key, required this.shop});
  final Shop shop;

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Lantern Reef',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          brightness: Brightness.dark,
          scaffoldBackgroundColor: const Color(0xFF06121F),
          colorScheme: const ColorScheme.dark(primary: Color(0xFFFFC857), surface: Color(0xFF0B2236)),
          fontFamily: 'Baloo',
        ),
        home: HomeScreen(shop: shop),
      );
}
