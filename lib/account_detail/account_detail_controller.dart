import 'dart:async';

import 'package:collection/collection.dart';
import 'package:timeless_aa/app/common/utils/copy_to_clipboard.dart';
import 'package:timeless_aa/core/arch/ui/controller/base_controller.dart';
import 'package:timeless_aa/core/arch/ui/controller/controller_provider.dart';
import 'package:timeless_aa/core/arch/data/local/local_starage_provider.dart';
import 'package:timeless_aa/core/di/injector.dart';
import 'package:timeless_aa/core/reactive_v2/dynamic_to_obs_data.dart';
import 'package:timeless_aa/core/reactive_v2/obs_data.dart';
import 'package:timeless_aa/core/wallet/base_wallet.dart';
import 'package:timeless_aa/app/core_impl/analytics/analytics_events.dart';
import 'package:timeless_aa/app/layers/ui/predefined_navigation_list.dart';
import 'package:timeless_aa/app/core_impl/wallet/smart_account/smart_account_wallet.dart';
import 'package:timeless_aa/app/layers/ui/component/sheet/recovery_alert/recovery_enum.dart';

class AccountDetailController extends BaseController
    with
        WalletsControllerProvider,
        LocalStorageProvider,
        AuthControllerProvider,
        SettingProvider {
  AccountDetailController({
    required this.wallet,
    required this.isPushedFromAccountDetail,
  });

  // --- Member Variables ---

  BaseWallet wallet;
  final bool isPushedFromAccountDetail;

  // --- State Variables ---

  final isChangingActiveState = listenable(false);

  // --- State Computed ---

  late final linkedWallet = listenableComputed(() {
    if (wallet is SmartAccountWallet) {
      return wallet.parent;
    }
    return walletsController.allAaAccounts.value.firstWhereOrNull(
        (account) => account.parent?.address == wallet.address);
  });

  late final isAccountToggleDisabled = listenableComputed(
    () =>
        wallet.isActive && !isChangingActiveState.value ||
        !wallet.isActive && isChangingActiveState.value,
  );

  late final isDomainOwned = listenableComputed(() {
    if (walletsController.resolverV2Mapping.status == ObsDataStatus.success) {
      return walletsController.checkEnsDomainOwned(wallet: wallet);
    }
    return null;
  });

  late final _willPopAlertSheet = listenableComputed(
    () =>
        (settingController.privateKeyAlert.value
                ?.difference(DateTime.now())
                .inDays
                .abs() ??
            31) >
        30,
  );

  // --- Methods ---

  toggleAccountActivation() async {
    if (walletsController.allActiveAccounts.value.length == 1 &&
        wallet.isActive) {
      nav.showSnackBar(message: "You can't disable the last account");
      return;
    }

    isChangingActiveState.value = true;
    try {
      await authController.toggleAccountActivation(wallet, !wallet.isActive);
      ana.performAction(
          AccountActivationSuccessEvent(EvAccountType.fromWallet(wallet)));
      nav.showSnackBar(
          message:
              "Account ${wallet.isActive ? 'enabled' : 'disabled'} successfully");
      return;
    } catch (error) {
      ana.performAction(AccountActivationErrorEvent(
        EvAccountType.fromWallet(wallet),
        error: error,
      ));
      nav.showSnackBar(error: error);
    } finally {
      isChangingActiveState.value = false;
    }
  }

  Future<void> copyAddressToClipBoard() async {
    await wallet.address
        .copyTextToClipboard(customMessage: 'Wallet address copied');
  }

  void toRecoveryPrivateKey() {
    if (_willPopAlertSheet.value) {
      nav.showRecoveryAlert(
        type: RecoveryType.privateKey,
        wallet: wallet,
      );
    } else {
      nav.toPrivateKey(wallet: wallet);
    }
  }

  @override
  FutureOr<void> onDispose() {}
}
