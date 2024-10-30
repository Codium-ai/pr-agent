import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_mobx/flutter_mobx.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:timeless_aa/app/common/extensions/base_wallet_extension.dart';
import 'package:timeless_aa/app/common/ui/color/color.dart';
import 'package:timeless_aa/app/common/ui/font/font.dart';
import 'package:timeless_aa/app/common/ui/size/size_extension.dart';
import 'package:timeless_aa/app/common/utils/wallet_address_format.dart';
import 'package:timeless_aa/core/arch/ui/controller/controller_provider.dart';
import 'package:timeless_aa/core/arch/data/local/local_starage_provider.dart';
import 'package:timeless_aa/core/di/injector.dart';
import 'package:timeless_aa/core/wallet/eoa/eoa_wallet.dart';
import 'package:timeless_aa/app/layers/ui/predefined_navigation_list.dart';
import 'package:timeless_aa/app/core_impl/wallet/smart_account/smart_account_wallet.dart';
import 'package:timeless_aa/app/layers/ui/component/page/account_detail/account_detail_controller.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/claim_username_widget/claim_username_button.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/common/container_wrapper.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/custom_buton/cta_button.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/custom_image_loader/image_loader.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/header/header_view.dart';

class AccountDetailPage extends StatelessWidget
    with
        ControllerProvider<AccountDetailController>,
        LocalStorageProvider,
        WalletsControllerProvider {
  const AccountDetailPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            SafeArea(bottom: false, child: _headerBar),
            Expanded(child: _contentView()),
            _disableButton.marginSymmetric(vertical: 8.hMin),
          ],
        ),
      ),
    );
  }

  Widget get _headerBar => Observer(
        builder: (context) {
          final ctrl = controller(context);
          final cacheWalletName = walletsController
              .walletNameCacheMap.value[ctrl.wallet.id];
          final userName = walletsController.profileDataMapping
              .value?[ctrl.wallet.address.toLowerCase()]?.username;
          return HeaderView(
            title: cacheWalletName ?? userName ?? ctrl.wallet.name,
            leftAction: HeaderAction.back,
          );
        },
      );

  Widget _contentView() => Observer(
        builder: (context) {
          final ctrl = controller(context);
          final linkedWallet = ctrl.linkedWallet.value;
          return SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            child: Column(
              children: [
                _infoAccountView(),
                SizedBox(height: 16.hMin),
                _buildButton(
                  textButton: 'Type',
                  rightAction: [
                    Row(
                      children: [
                        Text(
                          ctrl.wallet.displayType,
                          style: TextStyle(
                            fontSize: 14.spMin,
                            color: context.color.textColor.withOpacity(0.8),
                            fontFamily: Font.sfProText,
                            fontWeight: FontWeight.normal,
                          ),
                        ),
                        Icon(
                          CupertinoIcons.info,
                          size: 16.spMin,
                          color: context.color.textColor.withOpacity(0.8),
                        ).marginOnly(left: 5.wMin),
                      ],
                    ).marginOnly(right: 4.wMin),
                  ],
                ),
                _buildButton(
                  textButton: 'Address',
                  onTap: ctrl.copyAddressToClipBoard,
                  rightAction: [
                    Text(
                      ctrl.wallet.address.trimStringByCount(5),
                      style: TextStyle(
                        fontSize: 14.spMin,
                        color: context.color.textColor.withOpacity(0.8),
                        fontFamily: Font.sfProText,
                        fontWeight: FontWeight.normal,
                      ),
                    ),
                  ],
                ),
                if (ctrl.wallet is EOAWallet)
                  _buildButton(
                    textButton: 'Private key',
                    onTap: ctrl.toRecoveryPrivateKey,
                  ),
                if (linkedWallet != null)
                  _buildButton(
                    textButton: ctrl.wallet is SmartAccountWallet
                        ? 'Linked regular account'
                        : 'Linked smart account',
                    onTap: () {
                      if (linkedWallet.isActive) {
                        if (ctrl.isPushedFromAccountDetail) {
                          nav.back<void>();
                        } else {
                          nav.toAccountDetail(
                            linkedWallet,
                            isPushedFromAccountDetail: true,
                          );
                        }
                      }
                    },
                    rightAction: [
                      Text(
                        linkedWallet.address.trimStringByCount(5),
                        style: TextStyle(
                          fontSize: 14.spMin,
                          color: context.color.textColor.withOpacity(0.8),
                          fontFamily: Font.sfProText,
                          fontWeight: FontWeight.normal,
                        ),
                      ),
                      Icon(
                        Icons.chevron_right_sharp,
                        size: 20.spMin,
                        color: context.color.textColor.withOpacity(0.5),
                      ),
                    ],
                  ),
                if (ctrl.isDomainOwned.value == false)
                  ClaimUsernameButton(wallet: ctrl.wallet).marginOnly(
                    top: 95.hMin,
                    left: 16.wMin,
                    right: 12.wMin,
                  ),
              ],
            ),
          );
        },
      );

  Widget get _disableButton => Observer(
        builder: (context) {
          final ctrl = controller(context);
          return CtaButton(
            style: CtaButtonStyle.flat,
            padding: EdgeInsets.zero,
            onPressed: ctrl.isChangingActiveState.value
                ? null
                : ctrl.toggleAccountActivation,
            child: Builder(
              builder: (context) {
                return Container(
                  width: MediaQuery.of(context).size.width - 40.wMin,
                  height: 46.hMin,
                  decoration: BoxDecoration(
                    color: context.color.containerBackground,
                    borderRadius: BorderRadius.circular(21.rMin),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      if (ctrl.isChangingActiveState.value)
                        const CupertinoActivityIndicator()
                            .marginOnly(right: 10.wMin),
                      Text(
                        ctrl.isDisble.value ? 'Disable' : 'Enable',
                        style: TextStyle(
                          fontSize: 18.spMin,
                          color: context.color.errorTextColor,
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
          );
        },
      );

  Widget _infoAccountView() => Observer(
        builder: (context) {
          final ctrl = controller(context);
          return Column(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(50.rMin),
                child: ImageLoader(
                  url: ctrl.wallet.avatar,
                  width: 100.rMin,
                  height: 100.rMin,
                ),
              ).marginOnly(bottom: 10.hMin),
            ],
          );
        },
      ).paddingSymmetric(horizontal: 20.wMin, vertical: 10.hMin);

  Widget _buildButton({
    required String textButton,
    void Function()? onTap,
    List<Widget>? rightAction,
  }) =>
      Builder(
        builder: (context) {
          return CtaButton(
            onPressed: onTap,
            style: CtaButtonStyle.flat,
            padding: EdgeInsets.zero,
            child: ContainerWrapper(
              style: ContainerWrapperStyle.flat,
              borderRadius: BorderRadius.circular(10.rMin),
              padding: EdgeInsets.only(
                left: 16.rMin,
                right: 12.rMin,
                top: 16.rMin,
                bottom: 16.rMin,
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    textButton,
                    style: TextStyle(
                      fontSize: 16.spMin,
                      color: context.color.textColor,
                      fontFamily: Font.sfProText,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  Row(
                    children: rightAction ??
                        [
                          Icon(
                            Icons.chevron_right_sharp,
                            size: 20.spMin,
                            color: context.color.textColor.withOpacity(0.5),
                          ),
                        ],
                  ),
                ],
              ),
            ),
          );
        },
      ).paddingSymmetric(horizontal: 20.wMin, vertical: 4.hMin);
}
