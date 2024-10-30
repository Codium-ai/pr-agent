import 'dart:async';

import 'package:get/get_rx/src/rx_workers/utils/debouncer.dart';
import 'package:timeless_aa/core/arch/ui/controller/base_controller.dart';
import 'package:timeless_aa/core/arch/ui/controller/controller_provider.dart';
import 'package:timeless_aa/core/di/injector.dart';
import 'package:timeless_aa/app/layers/ui/predefined_navigation_list.dart';
import 'package:timeless_aa/app/layers/ui/component/page/qr_scanner/qr_scanner_handler.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/wallet/wallet_carousel.dart';
import 'package:timeless_aa/core/reactive_v2/dynamic_to_obs_data.dart';

class WalletController extends BaseController
    with
        WalletConnectProvider,
        WalletsControllerProvider,
        SettingProvider,
        ChainControllerProvider,
        WeatherControllerProvider {
  // --- Member Variables ---

  final walletCarouselState = WalletCarouselState();

  // --- State Variables ---

  final isLoading = listenable(false);

  final Debouncer debouncerSwitcher =
      Debouncer(delay: const Duration(milliseconds: 800));

  // --- State Computed ---

  late final hasWalletConnnectSessions = listenableComputed(
    () => walletConnect.sessions.value.isNotEmpty,
  );

  late final isWeatherLoading = listenableComputed(
    () =>
        weatherController.weatherData.isLoading ||
        weatherController.weatherData.isRefreshing ||
        weatherController.weatherData.value == null,
  );

  // --- Methods ---

  Future<void> scanQR() async {
    final text = await nav.toQrScanner();
    QRScannerHandler.handleScanResult(text);
  }

  @override
  FutureOr<void> onDispose() {
    debouncerSwitcher.cancel();
  }
}
