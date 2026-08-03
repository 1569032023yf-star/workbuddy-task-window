# HP BIOS F10 Manual Configuration
## 一键操作说明 (One-time operation guide)

### When / 何时操作
任意时间重启电脑，在 HP Logo 出现时按 **F10** 进入 BIOS Setup。

### Steps / 步骤 (仅需修改 2 个菜单项)

#### 1. Scheduled Power-On (定时开机)
导航到: **Advanced** → **Boot Options**

修改以下设置：
| Setting | 当前值 | 改为 |
|---------|--------|------|
| BIOS Power-On Hour | 14 (已通过WMI设置) | 确认是 14 |
| BIOS Power-On Minute | 40 (已通过WMI设置) | 确认是 40 |
| Sunday | Disable | **Enable** |
| Monday | Disable | **Enable** |
| Tuesday | Disable | **Enable** |
| Wednesday | Disable | **Enable** |
| Thursday | Disable | **Enable** |
| Friday | Disable | **Enable** |
| Saturday | Disable | **Enable** |

#### 2. After Power Loss (断电后行为)
导航到: **Advanced** → **Power Options** (或类似位置)

| Setting | 当前值 | 改为 |
|---------|--------|------|
| After Power Loss | Power Off | **Power On** |

### 注意
- **不要修改其他任何BIOS设置**
- 不需要清除或输入BIOS密码
- 不要刷BIOS
- 如果提示需要Setup Password但你不知道密码，选择 Cancel 退出
- 完成后按 **F10** 保存并退出

### After Completion / 完成后
重启进入 Windows，WorkBuddy 将自动通过 HP WMI 重新读取并验证所有值。
