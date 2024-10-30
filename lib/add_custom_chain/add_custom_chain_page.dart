import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_mobx/flutter_mobx.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get_utils/get_utils.dart';
import 'package:timeless_aa/app/common/ui/color/color.dart';
import 'package:timeless_aa/app/common/ui/font/font.dart';
import 'package:timeless_aa/app/common/ui/size/size_extension.dart';
import 'package:timeless_aa/core/arch/ui/controller/controller_provider.dart';
import 'package:timeless_aa/app/layers/ui/component/page/add_custom_chain/add_custom_chain_controller.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/custom_buton/action_icon_button.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/custom_buton/cta_button.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/custom_text_field/custom_text_field.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/header/header_view.dart';

class AddCustomChainPage extends StatelessWidget
    with ControllerProvider<AddCustomChainController> {
  const AddCustomChainPage({super.key});
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => FocusManager.instance.primaryFocus?.unfocus(),
      child: Scaffold(
        body: SafeArea(
          bottom: false,
          child: Column(
            children: [
              _header,
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    children: [
                      _description,
                      _customChainTextField.marginOnly(
                        top: 14.hMin,
                        left: 19.wMin,
                        right: 19.wMin,
                      ),
                      _addTokenButton.marginOnly(
                        top: 53.hMin,
                        bottom: MediaQuery.of(context).padding.bottom.hMin +
                            12.hMin,
                        left: 33.wMin,
                        right: 33.wMin,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget get _header => Builder(
        builder: (context) {
          return HeaderView(
            title: '',
            titleIcon: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  'Custom Network',
                  style: TextStyle(
                    fontSize: 17.spMin,
                    fontFamily: Font.sfProText,
                    color: context.color.textColor,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                ActionIconButton(
                  style: ActionIconButtonStyle.flat,
                  color: Colors.transparent,
                  onPressed: () {
                    showCupertinoDialog<void>(
                      context: context,
                      builder: (BuildContext context) => CupertinoAlertDialog(
                        title: const Text('Custom network'),
                        content: const Text(
                          'You can add EVM networks only. Only the EOA wallets (e.g., seed phrase / private key wallets, and keyless wallets) on the network are supported, i.e., Smart “AA” wallets are not supported on custom network.',
                        ),
                        actions: [
                          CupertinoDialogAction(
                            child: const Text('OK'),
                            onPressed: () => Navigator.of(context).pop(),
                          ),
                        ],
                      ),
                    );
                  },
                  iconData: CupertinoIcons.info_circle,
                  iconSize: 34.spMin,
                  iconColor: context.color.textColor.withOpacity(0.6),
                ),
              ],
            ).paddingOnly(left: 14.wMin),
            leftAction: HeaderAction.back,
          );
        },
      );

  Widget get _description => Builder(
        builder: (context) {
          return Container(
            width: double.infinity,
            decoration: ShapeDecoration(
              color: context.color.containerBackground,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12.rMin),
              ),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                SizedBox(
                  width: 19.wMin,
                  child: Text(
                    '􀁞',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: context.color.warningTextColor,
                      fontSize: 15.spMin,
                      fontFamily: Font.sfProText,
                    ),
                  ),
                ),
                SizedBox(width: 9.wMin),
                Expanded(
                  child: RichText(
                    text: TextSpan(
                      style: TextStyle(
                        fontSize: 15.spMin,
                        fontFamily: Font.sfProText,
                        color: context.color.subTextColor,
                      ),
                      children: _richTextChain(context),
                    ),
                  ),
                ),
              ],
            ).paddingAll(18.rMin),
          ).marginSymmetric(
            horizontal: 14.wMin,
          );
        },
      );

  List<InlineSpan> _richTextChain(BuildContext context) => [
        const TextSpan(text: 'Always '),
        TextSpan(
          text: 'DYOR. ',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: context.color.warningTextColor,
          ),
        ),
        const TextSpan(
          text: 'Make sure you know what you’re doing. '
              'Anyone can create a ',
        ),
        TextSpan(
          text: 'malicious ',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: context.color.warningTextColor,
          ),
        ),
        const TextSpan(
          text: 'network on a whim, including ',
        ),
        TextSpan(
          text: 'fake ',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: context.color.warningTextColor,
          ),
        ),
        const TextSpan(
          text: 'versions of existing network. '
              'Only add custom networks you trust.',
        ),
      ];

  Widget get _customChainTextField => Column(
        children: [
          _chainIDField.marginOnly(bottom: 16.hMin),
          _networkNameField.marginOnly(bottom: 16.hMin),
          _currencySymbolField.marginOnly(bottom: 16.hMin),
          _rpcUrlField.marginOnly(bottom: 16.hMin),
          _blockExplorerField.marginOnly(bottom: 16.hMin),
          _coinGeckoId,
        ],
      );

  Widget get _chainIDField => Observer(
        builder: (context) {
          final ctrl = controller(context);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(
                    'Network ID',
                    style: TextStyle(
                      fontSize: 15.spMin,
                      color: context.color.textColor.withOpacity(0.75),
                    ),
                  ),
                  AnimatedOpacity(
                    duration: const Duration(milliseconds: 300),
                    opacity: ctrl.isLoading.value ? 1 : 0,
                    child: Transform.scale(
                      scale: 0.7,
                      child: const CupertinoActivityIndicator(),
                    ).marginOnly(left: 4.wMin),
                  ),
                ],
              ).marginOnly(bottom: 6.hMin),
              CustomTextField(
                controller: ctrl.chainIDTextController,
                backgroundColor: context.color.sheetColor,
                inputType: TextInputType.number,
                hintText: 'eg., 1 for Ethereum',
              ),
            ],
          );
        },
      );

  Widget get _networkNameField => Builder(
        builder: (context) {
          final ctrl = controller(context);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Network Name',
                style: TextStyle(
                  fontSize: 15.spMin,
                  color: context.color.textColor.withOpacity(0.75),
                ),
              ).marginOnly(bottom: 6.hMin),
              CustomTextField(
                controller: ctrl.networkNameTextController,
                backgroundColor: context.color.sheetColor,
                hintText: 'Ethereum',
              ),
            ],
          );
        },
      );

  Widget get _blockExplorerField => Builder(
        builder: (context) {
          final ctrl = controller(context);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Block Explorer (Optional)',
                style: TextStyle(
                  fontSize: 15.spMin,
                  color: context.color.textColor.withOpacity(0.75),
                ),
              ).marginOnly(bottom: 6.hMin),
              CustomTextField(
                controller: ctrl.blockExplorerextController,
                backgroundColor: context.color.sheetColor,
                hintText: 'https://',
              ),
            ],
          );
        },
      );

  Widget get _rpcUrlField => Builder(
        builder: (context) {
          final ctrl = controller(context);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'RPC URL',
                style: TextStyle(
                  fontSize: 15.spMin,
                  color: context.color.textColor.withOpacity(0.75),
                ),
              ).marginOnly(bottom: 6.hMin),
              CustomTextField(
                controller: ctrl.rpcUrlTextController,
                backgroundColor: context.color.sheetColor,
                hintText: 'https://eth.llamarpc.com',
              ),
            ],
          );
        },
      );

  Widget get _currencySymbolField => Builder(
        builder: (context) {
          final ctrl = controller(context);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Currency Symbol',
                style: TextStyle(
                  fontSize: 15.spMin,
                  color: context.color.textColor.withOpacity(0.75),
                ),
              ).marginOnly(bottom: 6.hMin),
              IgnorePointer(
                child: CustomTextField(
                  controller: ctrl.currencySymbolTextController,
                  backgroundColor: context.color.sheetColor,
                  hintText: 'ETH',
                ),
              ),
            ],
          );
        },
      );

  Widget get _coinGeckoId => Builder(
        builder: (context) {
          final ctrl = controller(context);
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'CoinGecko ID (Optional)',
                style: TextStyle(
                  fontSize: 15.spMin,
                  color: context.color.textColor.withOpacity(0.75),
                ),
              ).marginOnly(bottom: 6.hMin),
              CustomTextField(
                controller: ctrl.coinGeckoIdTextController,
                backgroundColor: context.color.sheetColor,
                hintText: 'ethereum-name-service',
              ),
            ],
          );
        },
      );

  Widget get _addTokenButton => Builder(
        builder: (context) {
          final ctrl = controller(context);
          return Observer(
            builder: (context) {
              return Opacity(
                opacity: ctrl.enableAddButton.value && !ctrl.isLoading.value
                    ? 1
                    : 0.3,
                child: CtaButton(
                  padding: EdgeInsets.zero,
                  style: CtaButtonStyle.flat,
                  onPressed: ctrl.enableAddButton.value && !ctrl.isLoading.value
                      ? ctrl.addCustomChain
                      : null,
                  child: Builder(
                    builder: (context) {
                      return Container(
                        width: MediaQuery.of(context).size.width - 66.wMin,
                        height: 48.hMin,
                        decoration: BoxDecoration(
                          color: context.color.containerBackground,
                          borderRadius: BorderRadius.circular(21.rMin),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              CupertinoIcons.add,
                              color: context.color.commonGradientColors.last,
                              size: 17.rMin,
                            ),
                            Text(
                              'Add Network',
                              style: TextStyle(
                                fontSize: 17.spMin,
                                color: context.color.commonGradientColors.last,
                                fontFamily: Font.sfProText,
                              ),
                            ),
                          ],
                        ),
                      );
                    },
                  ),
                ),
              );
            },
          );
        },
      );
}
