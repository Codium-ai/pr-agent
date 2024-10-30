import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_mobx/flutter_mobx.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:flutter_svg/svg.dart';
import 'package:get/get.dart';
import 'package:provider/provider.dart';
import 'package:timeless_aa/app/common/datetime/predefined_date_format.dart';
import 'package:timeless_aa/app/common/ui/color/color.dart';
import 'package:timeless_aa/app/common/ui/font/font.dart';
import 'package:timeless_aa/app/common/ui/image/image_local.dart';
import 'package:timeless_aa/app/common/ui/size/size_extension.dart';
import 'package:timeless_aa/app/common/utils/number_format.dart';
import 'package:timeless_aa/app/common/utils/onramp_geo_restriction.dart';
import 'package:timeless_aa/app/layers/ui/component/page/wallet_selector/wallet_selector_controller.dart';
import 'package:timeless_aa/app/layers/ui/component/page/wallet_selector/wallet_selector_page.dart';
import 'package:timeless_aa/core/arch/ui/controller/controller_provider.dart';
import 'package:timeless_aa/core/arch/ui/view/base_provider.dart';
import 'package:timeless_aa/core/di/injector.dart';
import 'package:timeless_aa/app/core_impl/intent_flow/multiple_steps/send_intent_flow.dart';
import 'package:timeless_aa/app/layers/ui/predefined_navigation_list.dart';
import 'package:timeless_aa/app/layers/ui/component/page/wallet/wallet_controller.dart';
import 'package:timeless_aa/app/layers/ui/component/page/weather_unit_setting/weather_unit.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/common/container_wrapper.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/custom_buton/action_icon_button.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/custom_buton/cta_button.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/custom_image_loader/image_loader.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/placeholder/placeholder_widget.dart';
import 'package:timeless_aa/app/layers/ui/component/sheet/wallet_menu/wallet_menu_sheet.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/wallet/wallet_carousel.dart';

class WalletPage extends StatelessWidget
    with
        ControllerProvider<WalletController>,
        AppControllerProvider,
        SettingProvider,
        WalletsControllerProvider,
        DeeplinkControllerProvider,
        HomeControllerProvider {
  const WalletPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Observer(
          builder: (context) {
            return Column(
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _infoBlock.marginOnly(top: 5.hMin),
                    const Spacer(),
                    _scanBtn.marginOnly(
                      top: settingController.tabBarVisibility.value
                          ? 7.hMin
                          : 9.hMin,
                    ),
                    _walletSelector,
                  ],
                ),
                _actionBar.marginOnly(
                  left: 37.wMin,
                  right: 36.wMin,
                  top: settingController.tabBarVisibility.value
                      ? 20.hMin
                      : 30.hMin,
                  bottom: settingController.tabBarVisibility.value
                      ? 25.hMin
                      : 38.hMin,
                ),
                Expanded(
                  child: _walletCarousel,
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget get _walletSelector => BaseProvider(
        ctrl: WalletSelectorController(
          homeController.walletKey,
        ),
        child: WalletSelectorPage(
          avatarSize: 44.rMin,
        ).marginOnly(
          top: settingController.tabBarVisibility.value ? 7.hMin : 9.hMin,
          left: 10.wMin,
          right: 11.wMin,
        ),
      );

  Widget get _infoBlock => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _currentDateTxt.marginOnly(right: 8.wMin, left: 23.wMin),
          _balanceBlock.marginOnly(right: 23.wMin),
        ],
      );

  Widget get _scanBtn => Builder(
        builder: (context) {
          final ctrl = controller(context);
          return Observer(
            builder: (context) {
              return ActionIconButton(
                color: Colors.white.withOpacity(0.08),
                icon: ctrl.hasWalletConnnectSessions.value
                    ? SvgPicture.asset(
                        LocalImageRes.appBadgeCheckMark,
                        colorFilter: ColorFilter.mode(
                          context.color.textColor,
                          BlendMode.srcIn,
                        ),
                        width: 26.rMin,
                        height: 26.rMin,
                      )
                    : null,
                iconData: ctrl.hasWalletConnnectSessions.value
                    ? null
                    : CupertinoIcons.viewfinder,
                iconSize: 44.rMin,
                onPressed: ctrl.scanQR,
              );
            },
          );
        },
      );

  Widget get _actionBar => Observer(
        builder: (context) {
          return Row(
            children: [
              Opacity(
                opacity: OnrampGeoRestriction.isGeoRetricted ? 0.3 : 1,
                child: ActionIconButton(
                  color: Colors.white.withOpacity(0.08),
                  iconData: CupertinoIcons.creditcard,
                  title: 'Buy',
                  onPressed: deeplinkController.openBuyFlow,
                ),
              ),
              const Spacer(),
              ActionIconButton(
                  color: Colors.white.withOpacity(0.08),
                  iconData: CupertinoIcons.qrcode,
                  style: ActionIconButtonStyle.neumorphic,
                  title: 'Receive',
                  onPressed: () {
                    final currentWallet = walletsController.currentWallet.value;
                    if (currentWallet != null) {
                      nav.toReceive(currentWallet);
                    }
                  }),
              const Spacer(),
              // ActionIconButton(
              //     color: Colors.white.withOpacity(0.08),
              //     icon: Padding(
              //       padding: EdgeInsets.only(right: 2.wMin, top: 2.hMin),
              //       child: Icon(
              //         CupertinoIcons.paperplane,
              //         size: 32.rMin,
              //       ),
              //     ),
              //     title: 'Send',
              //     style: ActionIconButtonStyle.neumorphic,
              //     onPressed: () {
              //       injector.nav.toTransactionProcessModal(
              //         flow: SendIntentFlow(),
              //       );
              //     }),
              ActionIconButton(
                color: Colors.white.withOpacity(0.08),
                iconData: CupertinoIcons.arrow_swap,
                title: 'Exchange',
                onPressed: () {
                  final wallet = walletsController.currentWallet.value;
                  if (wallet == null) return;
                  nav.bottomSheetExchangeMenu(
                    menuList: menuList,
                    wallet: wallet,
                    snapSizes: 0.48,
                  );
                },
              ),
            ],
          );
        },
      );

  Widget get _currentDateTxt => Builder(builder: (context) {
        return Row(
          children: [
            CtaButton(
              style: CtaButtonStyle.flat,
              color: Colors.transparent,
              onPressed: () =>
                  appController.refresh(shouldStopRunningTask: true),
              child: Row(
                children: [
                  Text(
                    PredefinedDateFormat.date
                        .format(DateTime.now())
                        .toUpperCase(),
                    style: TextStyle(
                      fontFamily: Font.sfProText,
                      color: context.color.textColor,
                      fontSize: 14.spMin,
                    ),
                  ),
                  _weather,
                ],
              ),
            ),
            Observer(builder: (context) {
              return AnimatedOpacity(
                duration: const Duration(milliseconds: 300),
                opacity: appController.isLoading.value ? 1 : 0,
                child: SizedBox(
                  height: 14.hMin,
                  child: const CupertinoActivityIndicator(),
                ).marginOnly(left: 8),
              );
            }),
          ],
        );
      });

  Widget get _weather => Observer(
        builder: (context) {
          final ctrl = controller(context);
          if (!ctrl.settingController.isWeatherEnable.value ||
              ctrl.isWeatherLoading.value) {
            return const SizedBox.shrink();
          }

          final temp = ctrl.settingController.weatherUnitType.value ==
                  WeatherUnitType.farenheit
              ? ctrl.weatherController.weatherData.value?.main.temp
                  .round()
                  .toString()
              : ctrl.weatherController.weatherData.value?.main.tempCelsius
                  .round()
                  .toString();
          return Row(
            children: [
              ImageLoader(
                url:
                    'https://openweathermap.org/img/wn/${ctrl.weatherController.weatherData.value?.weather.firstOrNull?.icon}@2x.png',
                height: 35.hMin,
                width: 35.wMin,
              ),
              Text(
                '${temp ?? ''}${ctrl.settingController.weatherUnitType.value.symbol}',
                style: TextStyle(
                  fontFamily: Font.sfProText,
                  color: context.color.textColor,
                  fontSize: 14.spMin,
                ),
              ),
            ],
          );
        },
      );

  Widget get _balanceBlock => Observer(
        builder: (context) => CtaButton(
          onPressed: () => settingController.hideBalance.value =
              !settingController.hideBalance.value,
          style: CtaButtonStyle.flat,
          color: context.color.containerBackground,
          child: Container(
            padding:
                EdgeInsets.symmetric(horizontal: 15.wMin, vertical: 8.hMin),
            color: context.color.primaryBackground,
            child: Stack(
              alignment: AlignmentDirectional.centerStart,
              children: [
                IgnorePointer(
                  ignoring: !settingController.hideBalance.value,
                  child: AnimatedOpacity(
                    opacity: settingController.hideBalance.value ? 1 : 0,
                    duration: const Duration(milliseconds: 200),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          height: 46.hMin,
                          width: 142.wMin,
                          child: _hiddenBalanceTxt,
                        ),
                        _showBalanceDesc.marginOnly(top: 5.hMin, left: 8.wMin),
                      ],
                    ),
                  ),
                ),
                IgnorePointer(
                  ignoring: settingController.hideBalance.value,
                  child: AnimatedOpacity(
                    opacity: settingController.hideBalance.value ? 0 : 1,
                    duration: const Duration(milliseconds: 200),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(
                          height: 48.hMin,
                          child: _displayBalanceTxt,
                        ),
                        _totalBalanceDesc.marginOnly(
                          bottom: 2.hMin,
                          left: 3.wMin,
                        ),
                      ],
                    ).marginOnly(left: 5.wMin),
                  ),
                )
              ],
            ),
          ),
        ),
      );

  Widget get _displayBalanceTxt => Observer(
        builder: (context) {
          final totalUsdBalance =
              walletsController.totalUsdBalance.value?.formattedNumber;
          return ContainerWrapper(
            padding: EdgeInsets.zero,
            style: ContainerWrapperStyle.flat,
            color: context.color.primaryBackground,
            child: totalUsdBalance != null
                ? SizedBox(
                    // TODO: 200.wMin is a magic number, need to be refactored
                    // Ideally, it should be expand to the max width of parent
                    width: 200.wMin,
                    child: FittedBox(
                      alignment: Alignment.centerLeft,
                      child: Text(
                        '\$$totalUsdBalance',
                        maxLines: 1,
                        style: TextStyle(
                          color: context.color.textColor,
                          fontWeight: FontWeight.normal,
                          fontSize: 32.spMin,
                        ),
                      ),
                    ),
                  )
                : SizedBox(
                    width: 142.wMin,
                    child: const PlaceholderWidget(
                      type: PlaceholderType.balance,
                      size: PlaceholderSize.large,
                    ),
                  ),
          );
        },
      );

  Widget get _hiddenBalanceTxt => Builder(
        builder: (context) {
          return ContainerWrapper(
            padding: EdgeInsets.symmetric(horizontal: 16.wMin),
            style: ContainerWrapperStyle.neumorphicEmboss,
            borderRadius: BorderRadius.circular(22.rMin),
            color: context.color.primaryBackground,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(6, (index) => index + 1)
                  .map((_) => Container(
                        height: 10.rMin,
                        width: 10.rMin,
                        decoration: BoxDecoration(
                          color: context.color.textColor,
                          shape: BoxShape.circle,
                        ),
                      ).marginSymmetric(horizontal: 3.wMin))
                  .toList(),
            ),
          );
        },
      );

  Widget get _totalBalanceDesc => Builder(
      builder: (context) => Text(
            'TOTAL BALANCE',
            style: TextStyle(
                fontFamily: Font.sfProText,
                color: context.color.textColor.withOpacity(0.6),
                fontSize: 14.spMin),
          ));

  Widget get _showBalanceDesc => Builder(
      builder: (context) => Row(
            children: [
              Text(
                'SHOW BALANCE',
                style: TextStyle(
                    fontFamily: Font.sfProText,
                    color: context.color.textColor.withOpacity(0.6),
                    fontSize: 14.spMin),
              ),
              Transform.translate(
                offset: const Offset(0, -1),
                child: Icon(
                  CupertinoIcons.eye_fill,
                  color: context.color.textColor,
                  size: 18.rMin,
                ).marginOnly(left: 5.wMin),
              ),
            ],
          ));

  Widget get _walletCarousel => ChangeNotifierProvider(
        create: (context) => controller(context).walletCarouselState,
        child: WalletCarousel(),
      );
}

extension ExchangeMenuList on WalletPage {
  List<WalletMenuModel> get menuList => [
        WalletMenuModel(
          title: 'Buy',
          iconData: CupertinoIcons.creditcard,
          secondTitle: 'Buy or transfer crypto',
          onPress: deeplinkController.openBuyFlow,
          opacity: OnrampGeoRestriction.isGeoRetricted ? 0.3 : 1,
        ),
        WalletMenuModel(
          title: 'Receive',
          iconData: CupertinoIcons.qrcode,
          secondTitle: 'Copy your address',
          onPress: () {
            final currentWallet = walletsController.currentWallet.value;
            if (currentWallet != null) {
              nav.toReceive(currentWallet);
            }
          },
        ),
        WalletMenuModel(
          title: 'Send',
          iconData: CupertinoIcons.paperplane,
          secondTitle: 'Send crypto to any wallet',
          onPress: () => nav.toTransactionProcessModal(
            flow: SendIntentFlow(),
          ),
        ),
        WalletMenuModel(
          title: 'Swap',
          iconData: CupertinoIcons.arrow_swap,
          secondTitle: 'Exchange for another token',
          onPress: nav.toSwapPage,
        ),
        // TODO: Hide until DeFi integrated
        // WalletMenuModel(
        //   title: 'Earn',
        //   iconData: CupertinoIcons.percent,
        //   secondTitle: 'Earn rewards on your crypto',
        //   onPress: nav.toSwapPage,
        // ),
      ];
}
