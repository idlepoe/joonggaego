import 'package:flutter_test/flutter_test.dart';
import 'package:get/get.dart';
import 'package:joonggaego/app/modules/home/bindings/home_binding.dart';
import 'package:joonggaego/app/modules/home/views/home_view.dart';

void main() {
  testWidgets('HomeView builds', (WidgetTester tester) async {
    Get.testMode = true;
    HomeBinding().dependencies();
    await tester.pumpWidget(const GetMaterialApp(home: HomeView()));
    expect(find.byType(HomeView), findsOneWidget);
    Get.reset();
  });
}
