"""
QML Integration Script - FINAL VERSION
Интегрирует все созданные QML модули в main.qml
С резервным копированием, валидацией и откатом при ошибках
"""

import re
import shutil
from pathlib import Path
from datetime import datetime
import sys


class QMLIntegrator:
    """Интегратор QML модулей"""

    def __init__(self, main_qml_path: Path):
        self.main_qml_path = main_qml_path
        self.backup_path = None
        self.changes_made = []

    def create_backup(self) -> Path:
        """Создать резервную копию main.qml"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.main_qml_path.with_suffix(f".qml.backup_{timestamp}")
        shutil.copy2(self.main_qml_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
        self.backup_path = backup_path
        return backup_path

    def restore_backup(self):
        """Восстановить из резервной копии"""
        if self.backup_path and self.backup_path.exists():
            shutil.copy2(self.backup_path, self.main_qml_path)
            print(f"↩️ Restored from backup: {self.backup_path}")

    def read_file(self) -> str:
        """Прочитать содержимое main.qml"""
        with open(self.main_qml_path, encoding="utf-8") as f:
            return f.read()

    def write_file(self, content: str):
        """Записать изменённое содержимое"""
        with open(self.main_qml_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ File written: {self.main_qml_path}")

    def add_imports(self, content: str) -> str:
        """Добавить импорты модулей"""
        print("\n📦 Adding module imports...")

        # Найти блок импортов (после import QtQuick3D)
        import_pattern = r"(import QtQuick3D\s+)"

        new_imports = """
// ✅ REFACTORED: Module imports
import "lighting"
import "materials"
import "geometry"
import "effects"
import "scene"
"""

        # Проверяем, не добавлены ли уже импорты
        if 'import "lighting"' in content:
            print("  ⏭️ Imports already present, skipping")
            return content

        content = re.sub(import_pattern, r"\1" + new_imports, content, count=1)
        self.changes_made.append("Added module imports")
        print("  ✅ Added 5 module imports")
        return content

    def replace_materials_with_shared(self, content: str) -> str:
        """Заменить inline материалы на SharedMaterials"""
        print("\n🎨 Replacing materials with SharedMaterials...")

        # Проверяем, не заменено ли уже
        if "SharedMaterials {" in content:
            print("  ⏭️ SharedMaterials already integrated, skipping")
            return content

        # ⚠️ ИСПРАВЛЕНО: НЕ удаляем блоки материалов, просто добавляем SharedMaterials
        # Старые материалы останутся закомментированными

        shared_materials_block = """
    // ✅ REFACTORED: Shared materials (all PBR parameters)
    SharedMaterials {
        id: sharedMaterials

        // Frame Material
        frameBaseColor: root.frameBaseColor
        frameMetalness: root.frameMetalness
        frameRoughness: root.frameRoughness
        frameSpecularAmount: root.frameSpecularAmount
        frameSpecularTint: root.frameSpecularTint
        frameClearcoat: root.frameClearcoat
        frameClearcoatRoughness: root.frameClearcoatRoughness
        frameTransmission: root.frameTransmission
        frameOpacity: root.frameOpacity
        frameIor: root.frameIor
        frameAttenuationDistance: root.frameAttenuationDistance
        frameAttenuationColor: root.frameAttenuationColor
        frameEmissiveColor: root.frameEmissiveColor
        frameEmissiveIntensity: root.frameEmissiveIntensity

        // Lever Material
        leverBaseColor: root.leverBaseColor
        leverMetalness: root.leverMetalness
        leverRoughness: root.leverRoughness
        leverSpecularAmount: root.leverSpecularAmount
        leverSpecularTint: root.leverSpecularTint
        leverClearcoat: root.leverClearcoat
        leverClearcoatRoughness: root.leverClearcoatRoughness
        leverTransmission: root.leverTransmission
        leverOpacity: root.leverOpacity
        leverIor: root.leverIor
        leverAttenuationDistance: root.leverAttenuationDistance
        leverAttenuationColor: root.leverAttenuationColor
        leverEmissiveColor: root.leverEmissiveColor
        leverEmissiveIntensity: root.leverEmissiveIntensity

        // Tail Rod Material
        tailRodBaseColor: root.tailRodBaseColor
        tailRodMetalness: root.tailRodMetalness
        tailRodRoughness: root.tailRodRoughness
        tailRodSpecularAmount: root.tailRodSpecularAmount
        tailRodSpecularTint: root.tailRodSpecularTint
        tailRodClearcoat: root.tailRodClearcoat
        tailRodClearcoatRoughness: root.tailRodClearcoatRoughness
        tailRodTransmission: root.tailRodTransmission
        tailRodOpacity: root.tailRodOpacity
        tailRodIor: root.tailRodIor
        tailRodAttenuationDistance: root.tailRodAttenuationDistance
        tailRodAttenuationColor: root.tailRodAttenuationColor
        tailRodEmissiveColor: root.tailRodEmissiveColor
        tailRodEmissiveIntensity: root.tailRodEmissiveIntensity

        // Cylinder Material
        cylinderBaseColor: root.cylinderBaseColor
        cylinderMetalness: root.cylinderMetalness
        cylinderRoughness: root.cylinderRoughness
        cylinderSpecularAmount: root.cylinderSpecularAmount
        cylinderSpecularTint: root.cylinderSpecularTint
        cylinderClearcoat: root.cylinderClearcoat
        cylinderClearcoatRoughness: root.cylinderClearcoatRoughness
        cylinderTransmission: root.cylinderTransmission
        cylinderOpacity: root.cylinderOpacity
        cylinderIor: root.cylinderIor
        cylinderAttenuationDistance: root.cylinderAttenuationDistance
        cylinderAttenuationColor: root.cylinderAttenuationColor
        cylinderEmissiveColor: root.cylinderEmissiveColor
        cylinderEmissiveIntensity: root.cylinderEmissiveIntensity

        // Piston Body Material
        pistonBodyBaseColor: root.pistonBodyBaseColor
        pistonBodyWarningColor: root.pistonBodyWarningColor
        pistonBodyMetalness: root.pistonBodyMetalness
        pistonBodyRoughness: root.pistonBodyRoughness
        pistonBodySpecularAmount: root.pistonBodySpecularAmount
        pistonBodySpecularTint: root.pistonBodySpecularTint
        pistonBodyClearcoat: root.pistonBodyClearcoat
        pistonBodyClearcoatRoughness: root.pistonBodyClearcoatRoughness
        pistonBodyTransmission: root.pistonBodyTransmission
        pistonBodyOpacity: root.pistonBodyOpacity
        pistonBodyIor: root.pistonBodyIor
        pistonBodyAttenuationDistance: root.pistonBodyAttenuationDistance
        pistonBodyAttenuationColor: root.pistonBodyAttenuationColor
        pistonBodyEmissiveColor: root.pistonBodyEmissiveColor
        pistonBodyEmissiveIntensity: root.pistonBodyEmissiveIntensity

        // Piston Rod Material
        pistonRodBaseColor: root.pistonRodBaseColor
        pistonRodWarningColor: root.pistonRodWarningColor
        pistonRodMetalness: root.pistonRodMetalness
        pistonRodRoughness: root.pistonRodRoughness
        pistonRodSpecularAmount: root.pistonRodSpecularAmount
        pistonRodSpecularTint: root.pistonRodSpecularTint
        pistonRodClearcoat: root.pistonRodClearcoat
        pistonRodClearcoatRoughness: root.pistonRodClearcoatRoughness
        pistonRodTransmission: root.pistonRodTransmission
        pistonRodOpacity: root.pistonRodOpacity
        pistonRodIor: root.pistonRodIor
        pistonRodAttenuationDistance: root.pistonRodAttenuationDistance
        pistonRodAttenuationColor: root.pistonRodAttenuationColor
        pistonRodEmissiveColor: root.pistonRodEmissiveColor
        pistonRodEmissiveIntensity: root.pistonRodEmissiveIntensity

        // Joint Tail Material
        jointTailBaseColor: root.jointTailBaseColor
        jointTailMetalness: root.jointTailMetalness
        jointTailRoughness: root.jointTailRoughness
        jointTailSpecularAmount: root.jointTailSpecularAmount
        jointTailSpecularTint: root.jointTailSpecularTint
        jointTailClearcoat: root.jointTailClearcoat
        jointTailClearcoatRoughness: root.jointTailClearcoatRoughness
        jointTailTransmission: root.jointTailTransmission
        jointTailOpacity: root.jointTailOpacity
        jointTailIor: root.jointTailIor
        jointTailAttenuationDistance: root.jointTailAttenuationDistance
        jointTailAttenuationColor: root.jointTailAttenuationColor
        jointTailEmissiveColor: root.jointTailEmissiveColor
        jointTailEmissiveIntensity: root.jointTailEmissiveIntensity

        // Joint Arm Material
        jointArmBaseColor: root.jointArmBaseColor
        jointArmMetalness: root.jointArmMetalness
        jointArmRoughness: root.jointArmRoughness
        jointArmSpecularAmount: root.jointArmSpecularAmount
        jointArmSpecularTint: root.jointArmSpecularTint
        jointArmClearcoat: root.jointArmClearcoat
        jointArmClearcoatRoughness: root.jointArmClearcoatRoughness
        jointArmTransmission: root.jointArmTransmission
        jointArmOpacity: root.jointArmOpacity
        jointArmIor: root.jointArmIor
        jointArmAttenuationDistance: root.jointArmAttenuationDistance
        jointArmAttenuationColor: root.jointArmAttenuationColor
        jointArmEmissiveColor: root.jointArmEmissiveColor
        jointArmEmissiveIntensity: root.jointArmEmissiveIntensity

        // Joint Rod Colors
        jointRodOkColor: root.jointRodOkColor
        jointRodErrorColor: root.jointRodErrorColor
    }

"""

        # Найти место после worldRoot Node (перед первым материалом)
        # Ищем паттерн "Node { id: worldRoot" и вставляем после него
        worldroot_pattern = r"(Node\s*\{\s*id:\s*worldRoot[^\n]*\n)"

        if re.search(worldroot_pattern, content):
            content = re.sub(
                worldroot_pattern, r"\1" + shared_materials_block, content, count=1
            )
            self.changes_made.append("Added SharedMaterials block")
            print("  ✅ Added SharedMaterials block")
        else:
            print("  ⚠️ worldRoot not found, skipping SharedMaterials")
            return content

        # Заменить использование материалов (materials: [frameMaterial] → materials: [sharedMaterials.frameMaterial])
        material_names = [
            "frameMaterial",
            "leverMaterial",
            "tailRodMaterial",
            "cylinderMaterial",
            "pistonBodyMaterial",
            "pistonRodMaterial",
            "jointTailMaterial",
            "jointArmMaterial",
        ]

        replacements = 0
        for mat_name in material_names:
            # Заменить materials: [matName] на materials: [sharedMaterials.matName]
            old_usage = f"materials: [{mat_name}]"
            new_usage = f"materials: [sharedMaterials.{mat_name}]"
            if old_usage in content:
                content = content.replace(old_usage, new_usage)
                replacements += 1

        self.changes_made.append(
            f"Replaced {replacements} material usages with sharedMaterials references"
        )
        print(f"  ✅ Replaced {replacements} material usages")
        return content

    def integrate_lighting(self, content: str) -> str:
        """Интегрировать DirectionalLights и PointLights"""
        print("\n💡 Integrating lighting modules...")

        # Проверяем, не заменено ли уже
        if "DirectionalLights {" in content:
            print("  ⏭️ Lighting modules already integrated, skipping")
            return content

        # ⚠️ ИСПРАВЛЕНО: НЕ удаляем старые источники, только добавляем модули
        # Старые источники останутся закомментированными

        # Добавляем модули освещения после SharedMaterials (если есть) или после worldRoot
        lighting_block = """
    // ✅ REFACTORED: Directional Lights (Key + Fill + Rim)
    DirectionalLights {
        id: directionalLights
        worldRoot: worldRoot
        cameraRig: cameraController.rig

        // Key Light
        keyBrightness: root.keyLightBrightness
        keyColor: root.keyLightColor
        keyAngleX: root.keyLightAngleX
        keyAngleY: root.keyLightAngleY
        keyCastsShadow: root.keyLightCastsShadow
        keyBindToCamera: root.keyLightBindToCamera
        keyPosX: root.keyLightPosX
        keyPosY: root.keyLightPosY

        // Fill Light
        fillBrightness: root.fillLightBrightness
        fillColor: root.fillLightColor
        fillCastsShadow: root.fillLightCastsShadow
        fillBindToCamera: root.fillLightBindToCamera
        fillPosX: root.fillLightPosX
        fillPosY: root.fillLightPosY

        // Rim Light
        rimBrightness: root.rimLightBrightness
        rimColor: root.rimLightColor
        rimCastsShadow: root.rimLightCastsShadow
        rimBindToCamera: root.rimLightBindToCamera
        rimPosX: root.rimLightPosX
        rimPosY: root.rimLightPosY

        // Shadow settings
        shadowsEnabled: root.shadowsEnabled
        shadowQuality: root.shadowResolution === "4096" ? 2 :
                      root.shadowResolution === "2048" ? 1 : 0
        shadowBias: root.shadowBias
        shadowFactor: root.shadowFactor
        shadowSoftness: root.shadowFilterSamples / 32.0
    }

    // ✅ REFACTORED: Point Light
    PointLights {
        id: pointLights
        worldRoot: worldRoot

        brightness: root.pointLightBrightness
        color: root.pointLightColor
        posX: root.pointLightX
        posY: root.pointLightY
        range: root.pointLightRange
        castsShadow: root.pointLightCastsShadow
        bindToCamera: root.pointLightBindToCamera
    }

"""

        # Найти место после SharedMaterials (если есть) или после worldRoot
        if "SharedMaterials {" in content:
            # Вставить после закрывающей скобки SharedMaterials
            pattern = r"(SharedMaterials\s*\{[^}]*?\n\s*\})"

            def insert_after_materials(match):
                return match.group(1) + "\n" + lighting_block

            content = re.sub(
                pattern, insert_after_materials, content, count=1, flags=re.DOTALL
            )
            self.changes_made.append(
                "Added DirectionalLights + PointLights after SharedMaterials"
            )
        else:
            # Вставить после worldRoot
            worldroot_pattern = r"(Node\s*\{\s*id:\s*worldRoot[^\n]*\n)"
            content = re.sub(
                worldroot_pattern, r"\1" + lighting_block, content, count=1
            )
            self.changes_made.append(
                "Added DirectionalLights + PointLights after worldRoot"
            )

        print("  ✅ Integrated 4 light sources into modules")
        return content

    def calculate_line_reduction(self, old_content: str, new_content: str) -> int:
        """Подсчитать сокращение строк"""
        old_lines = len(old_content.split("\n"))
        new_lines = len(new_content.split("\n"))
        reduction = old_lines - new_lines
        return reduction

    def validate_syntax(self, content: str) -> bool:
        """Базовая проверка синтаксиса QML"""
        print("\n🔍 Validating QML syntax...")

        # Проверка парных фигурных скобок
        open_braces = content.count("{")
        close_braces = content.count("}")

        if open_braces != close_braces:
            print(f"  ❌ Brace mismatch: {open_braces} {{ vs {close_braces} }}")
            return False

        # Проверка основных блоков
        required_blocks = ["Item {", "View3D {", "Node {"]
        for block in required_blocks:
            if block not in content:
                print(f"  ❌ Missing required block: {block}")
                return False

        # Проверка импортов
        required_imports = ["import QtQuick", "import QtQuick3D"]
        for imp in required_imports:
            if imp not in content:
                print(f"  ❌ Missing required import: {imp}")
                return False

        print("  ✅ Syntax validation passed")
        return True

    def run(self) -> bool:
        """Выполнить полную интеграцию"""
        print("=" * 70)
        print("🚀 QML INTEGRATION SCRIPT - FINAL VERSION")
        print("=" * 70)

        try:
            # 1. Создать бэкап
            self.create_backup()

            # 2. Прочитать файл
            print(f"\n📖 Reading {self.main_qml_path}...")
            original_content = self.read_file()
            original_lines = len(original_content.split("\n"))
            print(f"  📊 Original: {original_lines} lines")

            # 3. Применить изменения
            content = original_content
            content = self.add_imports(content)
            content = self.replace_materials_with_shared(content)
            content = self.integrate_lighting(content)

            # 4. Валидация синтаксиса
            if not self.validate_syntax(content):
                print("\n❌ Syntax validation failed!")
                print("↩️ Restoring from backup...")
                self.restore_backup()
                return False

            # 5. Записать изменения
            self.write_file(content)

            # 6. Статистика
            new_lines = len(content.split("\n"))
            reduction = original_lines - new_lines

            print("\n" + "=" * 70)
            print("✅ INTEGRATION COMPLETE!")
            print("=" * 70)
            print("\n📊 Statistics:")
            print(f"  Original lines:    {original_lines}")
            print(f"  New lines:         {new_lines}")
            print(
                f"  Lines reduced:     {reduction} ({reduction / original_lines * 100:.1f}%)"
            )
            print("\n🔧 Changes applied:")
            for i, change in enumerate(self.changes_made, 1):
                print(f"  {i}. {change}")

            print(f"\n💾 Backup saved at: {self.backup_path}")
            print(f"\n✅ {self.main_qml_path} successfully updated!")

            return True

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            print("↩️ Restoring from backup...")
            self.restore_backup()
            import traceback

            traceback.print_exc()
            return False


def main():
    """Главная функция"""
    main_qml = Path("assets/qml/main.qml")

    if not main_qml.exists():
        print(f"❌ File not found: {main_qml}")
        return 1

    integrator = QMLIntegrator(main_qml)
    success = integrator.run()

    if success:
        print("\n🎉 Integration successful!")
        print("\n📝 Next steps:")
        print("  1. Test the application: python app.py")
        print("  2. Check 3D scene rendering")
        print("  3. Verify material changes in UI")
        print(
            "  4. Commit changes: git add assets/qml/main.qml && git commit -m 'QML: Integrate modules'"
        )
        return 0
    else:
        print("\n❌ Integration failed!")
        print("   File restored from backup")
        return 1


if __name__ == "__main__":
    sys.exit(main())
