import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:flutter_screenutil/flutter_screenutil.dart';
import 'package:get/get.dart';
import 'package:timeless_aa/app/common/ui/color/color.dart';
import 'package:timeless_aa/app/common/ui/font/font.dart';
import 'package:timeless_aa/app/common/ui/size/size_extension.dart';
import 'package:timeless_aa/core/arch/ui/controller/controller_provider.dart';
import 'package:flutter_mobx/flutter_mobx.dart';
import 'package:timeless_aa/core/backup/service/backup_service.dart';
import 'package:timeless_aa/core/di/injector.dart';
import 'package:timeless_aa/app/layers/ui/global_controller/wallets/wallets_controller.dart';
import 'package:timeless_aa/app/layers/ui/predefined_navigation_list.dart';
import 'package:lottie/lottie.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/custom_buton/cta_button.dart';
import 'package:timeless_aa/app/layers/ui/component/widget/header/header_view.dart';

class BackupPage extends StatelessWidget with BackupControllerProvider {
  final WalletGroup walletGroup;
  BackupPage({super.key, required this.walletGroup});

  final backupService = inj.get<BackupService>();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          _headerBar,
          _content.marginAll(16.rMin),
        ]),
      ),
    );
  }

  Widget get _headerBar => const HeaderView(title: 'Backup');

  Widget get _content => Observer(
        builder: (context) {
          if (backupController.backupFilePath.value?[walletGroup.wallet.id] !=
              null) {
            return _buildContainer(child: _backedUpView);
          } else {
            return Column(
              children: [
                _buildContainer(child: _noBackupView),
              ],
            );
          }
        },
      );

  Widget _buildContainer({required Widget child}) => Builder(
        builder: (context) {
          return Container(
            height: MediaQuery.of(context).size.height * 0.7,
            decoration: BoxDecoration(
              color: context.color.containerBackground,
              borderRadius: BorderRadius.circular(13.rMin),
            ),
            child: child,
          );
        },
      );

  Widget get _noBackupView => _buildContainer(
        child: Builder(
          builder: (context) {
            return Stack(
              alignment: Alignment.center,
              children: [
                Column(
                  children: [
                    _buildTitle(
                      title: 'Backup to ${backupService.name}',
                    ).paddingOnly(top: 30.hMin, left: 14.wMin, right: 14.wMin),
                    _buildDescription(
                      description:
                          "Don't risk your money! \nBackup your wallet so you can \nrecover it if you lose this device.",
                    ).paddingOnly(top: 20.hMin, left: 34.wMin, right: 34.wMin),
                    const Spacer(),
                    _noBackupButton,
                  ],
                ),
                _lottieCircle,
              ],
            );
          },
        ),
      );

  Widget get _backedUpView => _buildContainer(
        child: Builder(
          builder: (context) {
            return Stack(
              alignment: Alignment.center,
              children: [
                Column(
                  children: [
                    _buildTitle(
                      title: 'Back up complete',
                    ).paddingOnly(top: 30.hMin, left: 14.wMin, right: 14.wMin),
                    _buildDescription(
                      description:
                          "If you lose this device, you can recover \nyour encrypted wallet backup from \niCloud using the password specified.",
                    ).paddingOnly(top: 20.hMin, left: 34.wMin, right: 34.wMin),
                    const Spacer(),
                    _backedUpButton,
                  ],
                ),
                Icon(
                  Icons.cloud_circle_rounded,
                  size: 100.spMin,
                  color: Colors.white,
                )
              ],
            );
          },
        ),
      );

  Widget _buildTitle({required String title}) => Builder(builder: (context) {
        return Text(
          title,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: context.color.textColor,
            fontSize: 28.spMin,
            fontFamily: Font.sfProText,
            fontWeight: FontWeight.w700,
          ),
        );
      });

  Widget _buildDescription({required String description}) =>
      Builder(builder: (context) {
        return Text(
          description,
          maxLines: null,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: context.color.textColor.withOpacity(0.8),
            fontSize: 14.spMin,
            fontFamily: Font.sfProText,
            fontWeight: FontWeight.w500,
          ),
        );
      });

  Widget get _lottieCircle => Transform.translate(
        offset: Offset(0, -29.hMin),
        child: Lottie.asset(
          'assets/lotties/circle-loading.json',
          repeat: true,
          width: 129.wMin,
          height: 113.hMin,
          fit: BoxFit.contain,
        ),
      );

  Widget _buildNermophismButton(
          {required Widget content, required Function() onTap}) =>
      Builder(builder: (context) {
        return CtaButton(
            onPressed: onTap,
            color: context.color.primaryBackground,
            style: CtaButtonStyle.flat,
            child: SizedBox(
              height: 48.hMin,
              child: content,
            )).paddingOnly(bottom: 12.hMin, right: 18.wMin, left: 18.wMin);
      });

  Widget get _noBackupButton => Builder(
        builder: (context) {
          return _buildNermophismButton(
            content: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.cloud_upload,
                  size: 18.spMin,
                  color: context.color.textColor,
                ).paddingOnly(right: 6.wMin),
                Builder(
                  builder: (context) {
                    return Text(
                      'Backup to ${backupService.name}',
                      style: TextStyle(
                        color: context.color.textColor,
                        fontFamily: Font.sfProText,
                        fontSize: 17,
                        fontWeight: FontWeight.w500,
                      ),
                    );
                  },
                ),
              ],
            ),
            onTap: () =>
                backupController.showBackupFlow(walletGroup: walletGroup),
          );
        },
      );

  Widget get _backedUpButton => Builder(
        builder: (context) {
          return _buildNermophismButton(
            content: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  CupertinoIcons.cloud_upload,
                  size: 18.spMin,
                  color: context.color.textColor,
                ).paddingOnly(right: 4.wMin),
                Builder(
                  builder: (context) {
                    return Text(
                      'Manage iCloud Backups',
                      style: TextStyle(
                        color: context.color.textColor,
                        fontFamily: Font.sfProText,
                        fontSize: 17,
                        fontWeight: FontWeight.w600,
                      ),
                    );
                  },
                ),
              ],
            ),
            onTap: () => nav.bottomSheetManageBackup(walletGroup: walletGroup),
          );
        },
      );
}
