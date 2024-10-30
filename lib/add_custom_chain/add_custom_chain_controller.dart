import 'dart:async';

import 'package:flutter/material.dart';
import 'package:timeless_aa/core/arch/ui/controller/base_controller.dart';
import 'package:timeless_aa/core/arch/ui/controller/controller_provider.dart';
import 'package:timeless_aa/core/di/injector.dart';
import 'package:timeless_aa/app/core_impl/exception/common_error.dart';
import 'package:timeless_aa/core/reactive_v2/dynamic_to_obs_data.dart';
import 'package:timeless_aa_api/core/service/model/response/chain.dart';
import 'package:timeless_aa_api/core/service/model/response/rpc_info.dart';

class AddCustomChainController extends BaseController
    with SettingProvider, AppControllerProvider, ChainControllerProvider {
  AddCustomChainController() {
    _initialize();
  }

  // --- Member Variables ---

  final chainIDTextController = TextEditingController();
  final networkNameTextController = TextEditingController();
  final blockExplorerextController = TextEditingController();
  final rpcUrlTextController = TextEditingController();
  final currencySymbolTextController = TextEditingController();
  final coinGeckoIdTextController = TextEditingController();

  Timer? _timer;

  EvmChain? _chainSelected;
  // --- State Variables ---

  final chainId = listenable('');

  final networkName = listenable('');

  final blockExplorer = listenable('');

  final rpcUrl = listenable('');

  final coinGeckoId = listenable('');

  final isLoading = listenable(false);

  // --- State Computed ---

  late final chainIDError = listenableComputed(
    () =>
        chainId.value.isNotEmpty &&
        networkName.value.isNotEmpty &&
        rpcUrl.value.isNotEmpty,
  );

  late final enableAddButton = listenableComputed(
    () =>
        chainId.value.isNotEmpty &&
        networkName.value.isNotEmpty &&
        rpcUrl.value.isNotEmpty,
  );

  // --- Methods ---

  void addCustomChain() {
    isLoading.value = true;
    final chainId = int.parse(chainIDTextController.text);
    if (_chainSelected == null) {
      nav.showSnackBar(error: CommonError.chainNotFound);
      isLoading.value = false;
      return;
    }
    final data = settingController.enableChains.value;
    if (data.customChains.any((chain) => chain.chainId == chainId) ||
        data.optionChains
            .any((chainId) => chainId.toString() == this.chainId.value)) {
      nav.showSnackBar(error: CommonError.chainAlreadyExists);
      isLoading.value = false;
      return;
    }
    if (_chainSelected == null) return;
    var rpcInfo = _chainSelected?.rpcInfo
            .where((rpc) => rpc.url.trim().isNotEmpty)
            .toList() ??
        [];
    if (rpcInfo.isEmpty) {
      rpcInfo = [RpcInfo(name: 'Default', url: rpcUrl.value, isOnline: true)];
    }
    final customChain = EvmChain(
      chainId: chainId,
      name: networkName.value,
      rpc: rpcUrl.value,
      coingeckoPlatformId: coinGeckoId.value.isEmpty ? null : coinGeckoId.value,
      blockExplorer: blockExplorer.value.isEmpty ? null : blockExplorer.value,
      testnet: _chainSelected?.testnet ?? false,
      createdAt: _chainSelected?.createdAt,
      updatedAt: _chainSelected?.updatedAt,
      icon: _chainSelected?.icon,
      rpcInfo: rpcInfo,
      tokens: _chainSelected?.tokens ?? [],
    );
    chainController.addCustomChain(chain: customChain);
    nav.back<void>();
  }

  @override
  FutureOr<void> onDispose() {
    chainIDTextController.dispose();
    networkNameTextController.dispose();
    blockExplorerextController.dispose();
    rpcUrlTextController.dispose();
    coinGeckoIdTextController.dispose();
    currencySymbolTextController.dispose();
    _timer?.cancel();
  }

  Future<void> _initialize() async => _addTextFieldListener();

  void _addTextFieldListener() {
    _addListener(chainIDTextController, _handleChainIDTextChange);
    _addListener(networkNameTextController, (text) => networkName.value = text);
    _addListener(
        blockExplorerextController, (text) => blockExplorer.value = text);
    _addListener(rpcUrlTextController, (text) => rpcUrl.value = text);
    _addListener(coinGeckoIdTextController, (text) => coinGeckoId.value = text);
  }

  void _handleChainIDTextChange(String text) {
    chainId.value = text;
    // Cancel any previous timer
    _timer?.cancel();
    if (chainId.value.isEmpty) {
      isLoading.value = false;
      return;
    }
    isLoading.value = true;
    // Start a new timer
    _timer = Timer(const Duration(seconds: 1), () async {
      try {
        final chain = await chainController.getCustomChain(
            chainId: int.parse(chainId.value));
        _chainSelected = chain;
        networkNameTextController.text = chain.name;
        rpcUrlTextController.text = chain.rpc;
        blockExplorerextController.text = chain.blockExplorer ?? '';
        currencySymbolTextController.text =
            chain.tokens.firstOrNull?.symbol ?? '';
        isLoading.value = false;
      } catch (error, stackTrace) {
        _chainSelected = null;
        isLoading.value = true;
        log.error(
          '[AddCustomToken] Fetching Custom Chain error: $error!',
          error: error,
          stackTrace: stackTrace,
        );
        nav.showSnackBar(error: CommonError.chainNotFound);
      }
    });
  }

  void _addListener(
    TextEditingController controller,
    dynamic Function(String) onChanged,
  ) =>
      controller.addListener(() {
        onChanged(controller.text);
      });
}
