import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// One non-consumable: Deep Pass opens the Twilight and Midnight seas.
const deepPassId = 'com.example.lanternreef.deeppass';

class Shop {
  Shop._(this.deepPass);
  bool deepPass;

  static Future<Shop> load() async {
    final prefs = await SharedPreferences.getInstance();
    return Shop._(prefs.getBool('deepPass') ?? false);
  }

  bool unlocked(bool seaIsFree) => seaIsFree || deepPass;

  Future<void> buy() async {
    final response = await InAppPurchase.instance.queryProductDetails({deepPassId});
    if (response.productDetails.isEmpty) return;
    await InAppPurchase.instance.buyNonConsumable(purchaseParam: PurchaseParam(productDetails: response.productDetails.first));
  }
}
