import 'package:get/get.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../../../config/app_config.dart';

class HomeController extends GetxController {
  late final WebViewController webViewController;

  final isLoading = true.obs;
  final loadProgress = 0.obs;

  @override
  void onInit() {
    super.onInit();
    webViewController = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onProgress: (progress) {
            loadProgress.value = progress;
            if (progress >= 100) {
              isLoading.value = false;
            }
          },
          onPageStarted: (_) => isLoading.value = true,
          onPageFinished: (_) => isLoading.value = false,
          onWebResourceError: (_) => isLoading.value = false,
        ),
      )
      ..loadRequest(Uri.parse(AppConfig.webAppUrl));
  }

  /// WebView 히스토리 뒤로가기. 처리했으면 true.
  Future<bool> goBackInWebView() async {
    if (await webViewController.canGoBack()) {
      await webViewController.goBack();
      return true;
    }
    return false;
  }
}
