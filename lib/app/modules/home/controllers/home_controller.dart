import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import 'package:get/get.dart';

import '../../../config/app_config.dart';

class HomeController extends GetxController {
  InAppWebViewController? webViewController;

  final isLoading = true.obs;
  final loadProgress = 0.obs;

  final initialUrlRequest = URLRequest(
    url: WebUri(AppConfig.webAppUrl),
  );

  final initialSettings = InAppWebViewSettings(
    javaScriptEnabled: true,
    useOnLoadResource: false,
  );

  void onWebViewCreated(InAppWebViewController controller) {
    webViewController = controller;
  }

  void onLoadStart() {
    isLoading.value = true;
  }

  void onLoadStop() {
    isLoading.value = false;
  }

  void onProgressChanged(int progress) {
    loadProgress.value = progress;
    if (progress >= 100) {
      isLoading.value = false;
    }
  }

  void onLoadError() {
    isLoading.value = false;
  }

  /// WebView 히스토리 뒤로가기. 처리했으면 true.
  Future<bool> goBackInWebView() async {
    final c = webViewController;
    if (c != null && await c.canGoBack()) {
      await c.goBack();
      return true;
    }
    return false;
  }
}
