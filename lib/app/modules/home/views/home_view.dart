import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:get/get.dart';

import '../controllers/home_controller.dart';

class HomeView extends GetView<HomeController> {
  const HomeView({super.key});

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) async {
        if (didPop) return;
        final handled = await controller.goBackInWebView();
        if (!handled) {
          await SystemNavigator.pop();
        }
      },
      child: Scaffold(
        body: SafeArea(
          child: Stack(
            children: [
              InAppWebView(
                initialUrlRequest: controller.initialUrlRequest,
                initialSettings: controller.initialSettings,
                onWebViewCreated: controller.onWebViewCreated,
                onLoadStart: (webView, url) => controller.onLoadStart(),
                onLoadStop: (webView, url) => controller.onLoadStop(),
                onProgressChanged: (webView, progress) =>
                    controller.onProgressChanged(progress),
                onReceivedError: (webView, request, error) =>
                    controller.onLoadError(),
                onReceivedHttpError: (webView, request, response) =>
                    controller.onLoadError(),
              ),
              Obx(() {
                if (!controller.isLoading.value) {
                  return const SizedBox.shrink();
                }
                return ColoredBox(
                  color: Theme.of(context).scaffoldBackgroundColor,
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const CircularProgressIndicator(),
                        if (controller.loadProgress.value > 0) ...[
                          const SizedBox(height: 16),
                          Text('${controller.loadProgress.value}%'),
                        ],
                      ],
                    ),
                  ),
                );
              }),
            ],
          ),
        ),
      ),
    );
  }
}
