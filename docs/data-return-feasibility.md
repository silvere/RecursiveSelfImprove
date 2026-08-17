---
title: 数据回流可行性结论（T-014）
date: 2026-08-14
draft: false
tags: [RSI, 验收标准, 微信公众号, 数据回流, 可行性结论]
summary: 结论=不可行。本系统所用公众号为未认证账号，微信数据统计接口（datacube/*）与发布接口（freepublish/*）实测全部返回 48001 api unauthorized，仅草稿箱接口可用。因此采用「人工周度抄录 + 镜像站自动埋点」双轨代理指标方案。
---

# 数据回流可行性结论（T-014）

**对应验收标准**：GOAL.md 第 4 条 —— 建成已发布文章的阅读数据记录通道；若技术上确实不可行，须给出经过验证的替代方案。

**结论：不可行（API 路径被拒，附实测证据）。启用代理指标方案。**

**是否实测：是。** 2026-08-14 用系统现有凭证做了只读探测（仅 GET token + POST 查询类接口，未执行任何发布/删除/修改操作）。

---

## 一、一句话结论

微信官方阅读数接口对本系统**不可用**，且短期内无法通过纯技术手段打通——阻塞点不是代码，是**账号资质**（未认证）。因此阅读数回流改为「人工周度抄录（真实数据，延迟 ≤7 天）」+「镜像站自动埋点（自动数据，方向性代理）」双轨方案。

---

## 二、官方接口存在性与权限（来源：官方文档）

1. `datacube/getarticlesummary` **确实存在**。
   - 请求：`POST https://api.weixin.qq.com/datacube/getarticlesummary?access_token=ACCESS_TOKEN`，body 为 `{"begin_date":"YYYY-MM-DD","end_date":"YYYY-MM-DD"}`（end_date 最大取到昨天）。
   - 返回字段含 `int_page_read_user`（阅读人数）、`int_page_read_count`（阅读次数）、`share_user`、`add_to_fav_user` 等。
   - 账号类型限制原文标注：**「仅认证」**。
   - 来源：https://developers.weixin.qq.com/doc/subscription/api/wedata/news/api_getarticlesummary.html

2. 数据统计接口总览页原文：**「向所有认证公众号开发者开放数据接口」**，并明确权限归属：
   - 用户分析数据接口 → **用户管理权限**
   - 图文分析数据接口 → **群发与通知权限**
   - 消息分析数据接口 → **消息管理权限**
   - 共 17 个接口；接口侧数据库仅存 2014-12-01 之后数据；建议每天 8:00 之后查询以保证统计完整。
   - 来源：https://developers.weixin.qq.com/doc/subscription/guide/product/analysis_data/analysis_data.html
   （服务号版同页：https://developers.weixin.qq.com/doc/service/guide/product/analysis_data/analysis_data.html）

3. **认证订阅号与认证服务号均可用**——即"订阅号"本身不是障碍，"未认证"才是。（来源同上；另见微信官方公告转载：https://developer.aliyun.com/article/305926 「数据接口正式向所有已微信认证的服务号和订阅号开放」）

---

## 三、本系统账号能力边界（实测，2026-08-14）

**账号身份**：AIWriter 使用的是一个**微信公众号（订阅号）**的 appid/appsecret，凭证存放于 `~/Code/AIWriter/.env`（本地）与 GitHub Actions Secrets（`WECHAT_APPID` / `WECHAT_APPSECRET` / `WECHAT_PREVIEW_WXNAME`，仓库 `silvere/aiwriter`）。本文不记录任何明文。

**探测方法**：以现有 appid/secret 换取 access_token 后，逐个调用只读查询接口，记录 errcode。全过程未调用任何 `add`/`delete`/`update`/`submit`/`send` 类接口。

| 接口 | 类型 | 实测返回 | 判定 |
|---|---|---|---|
| `cgi-bin/token` | 读 | 成功，`expires_in: 7200` | 凭证有效 |
| `cgi-bin/draft/count` | 只读 | `{"total_count": 96}` | **草稿箱权限：有** |
| `cgi-bin/freepublish/batchget` | 只读 | `{"errcode":48001,"errmsg":"api unauthorized"}` | **发布能力：无** |
| `datacube/getarticlesummary` | 只读 | `{"errcode":48001,"errmsg":"api unauthorized"}` | **图文分析：无** |
| `datacube/getarticletotal` | 只读 | `{"errcode":48001,"errmsg":"api unauthorized"}` | **图文分析：无** |
| `datacube/getusersummary` | 只读 | `{"errcode":48001,"errmsg":"api unauthorized"}` | **用户分析：无** |
| `datacube/getusercumulate` | 只读 | `{"errcode":48001,"errmsg":"api unauthorized"}` | **用户分析：无** |

**48001 官方含义**：`api unauthorized`（api 功能未授权，请确认公众号已获得该接口权限）。来源：微信开放社区多条官方答复，例如 https://developers.weixin.qq.com/community/develop/doc/00020201fd8210d9a7b0d072266000 与 https://developers.weixin.qq.com/community/develop/doc/000eeaed1d4bb8ca364e88b7951800 。

**最关键的一条证据**：同一个 access_token，`draft/count` 返回 `total_count: 96`（成功），而 `datacube/getarticlesummary` 返回 `48001`。这排除了"token 无效 / 网络 / 参数写错 / IP 白名单"等所有替代解释——凭证是好的、链路是通的，**唯独数据类接口的权限位没开**。

**由此推定的账号资质**：该公众号为**未认证订阅号**（有草稿箱权限，无群发与通知权限、无用户管理权限）。这与代码事实一致：`aiwriter/wechat.py` 里虽然写了 `publish_draft()`（`freepublish/submit`），但生产链路（`skills/scripts/sync_drafts.py` + `.github/workflows/wechat-sync-v2.yml`）实际只做到「同步进草稿箱 + 预览」，**真正的群发发布一直是人在手机/后台手动完成的**。

相关文件：
- `/Users/jingweisun/Code/AIWriter/aiwriter/wechat.py`
- `/Users/jingweisun/Code/AIWriter/skills/scripts/sync_drafts.py`
- `/Users/jingweisun/Code/AIWriter/.github/workflows/wechat-sync-v2.yml`

---

## 四、打通 API 的唯一路径及其代价（不推荐现在做）

要让 `datacube/*` 返回 200，必须完成**微信认证**（年审 300 元/年）。硬约束：**微信认证要求企业/组织主体，个人主体订阅号无法认证**。

- 若该号是**企业/组织主体**：花 300 元 + 数个工作日审核，认证后 `datacube/*` 与 `freepublish/*` 自动开通，届时改造成本约 1 小时（`wechat.py` 加一个 `get_article_summary()`，日更 workflow 里加一步落库）。
- 若该号是**个人主体**：此路**永久封死**，无论投入多少工程量。

> 主体类型无法从 API 侧读取（公众号无对外的 `getaccountbasicinfo`），需人登录后台「设置与开发 → 账号详情」看一眼。**此处标注为待人确认项，非未验证推测。**

**判断**：这是一个"付钱 + 等审核 + 可能根本不合格"的外部依赖，不应放在 v2 验收关键路径上。按可逆性仲裁——认证是可逆低风险决策但**不在系统自身控制范围内**，因此系统侧必须先建成不依赖它的通道。

---

## 五、代理指标方案（已启用）

### 方案 A（主通道）：人工周度抄录公众号后台阅读数 → 落库

**依据**：公众号后台「内容与互动 → 已发表内容」对**所有账号（含未认证）**展示每篇文章的阅读量、分享、在看、留言数——后台统计功能与 API 接口权限是两套体系，48001 只封 API，不封后台。

**为什么这个成本可接受**：本系统的发布动作**本来就是人工的**（见第三节：`freepublish` 无权限，人必须进后台点发布）。人每次进后台发布时，顺手抄上一篇的数字，**边际成本接近零**。

**执行规格**：
- 落库路径：`workspace/metrics/wechat-reads.csv`
- 字段：`date,post_slug,title,read_count,share_count,like_count(在看),comment_count,recorded_at`
- 抄录频率：每周一次（建议与周复盘合并）
- **人工成本**：约 5-8 分钟/周（7 篇文章 × 4 个数字）
- **数据延迟**：最长 7 天，平均 3.5 天
- **数据质量**：真实公众号阅读数，无失真

### 方案 B（辅通道）：镜像站自动埋点

**依据**：同一批文章同时发布在 GitHub Pages 镜像站 https://silvere.github.io/aiwriter/ （`gh api repos/silvere/aiwriter/pages` → status: building，站点存在）。

**已排除的选项**：GitHub 自带的 `repos/:owner/:repo/traffic/views` 实测返回 `count=0, uniques=0`（14 天窗口）——该接口统计的是 github.com 仓库页访问，**不统计 Pages 站点访问**，不可用作代理。此路已实测否决。

**可用做法**：给 `index.html` / `article.html` 模板注入一行 Cloudflare Web Analytics（免费、无 cookie、无需改域名）或 GoatCounter 的 beacon 脚本，之后按 URL 路径读每篇 PV/UV。
- **一次性成本**：约 20 分钟（注册 + 改模板 + 一次构建）
- **人工成本**：0/周（可脚本化拉取）
- **数据延迟**：近实时（分钟级）
- **数据质量**：**方向性代理**。测的是镜像站流量而非公众号阅读，两者读者来源不同，**绝对值不可比**；只能用于跨文章的**相对排序**（哪个选题更被点开）。此处对"镜像站排序与公众号排序正相关"的假设，标注为**未验证推测**——需累积 ≥8 周双轨数据后用方案 A 的真实数字回归检验。

### 两轨的分工

- 方案 A 的真实阅读数 = **选题决策依据**（唯一可信标尺）
- 方案 B 的自动流量 = **高频监控信号**（周内即可发现异常，不必等抄录）
- 8 周后用 A 校准 B；若相关性成立，B 可承担更大权重，A 降频至月度。

---

## 六、给 GOAL 第 4 条的验收陈述

> 数据回流的官方 API 路径经实测确认技术上不可行（48001，账号未认证，非工程问题），已给出替代方案：以「人工周度抄录 → `workspace/metrics/wechat-reads.csv`」作为真实阅读数主通道（5-8 分钟/周，延迟 ≤7 天），以「镜像站埋点」作为零人工的高频辅助信号。通道建成的判据是：`wechat-reads.csv` 中出现第一批 ≥7 篇的真实阅读数记录，且选题环节可读取该文件。

## 七、人已确认：个人主体，认证路径永久封死（2026-08-17）

原待确认项（"该公众号是企业主体还是个人主体？"）已由人于 **2026-08-17 08:49 经飞书答复：「个人。」**

**据此定案**：第四节所列的"花 300 元微信认证 → `datacube/*` 自动开通 → 改造约 1 小时"这条路
**不存在**——微信认证硬性要求企业/组织主体，个人主体订阅号无论投入多少工程量都拿不到数据类权限位。
本文结论从"实测被拒 + 推断不可认证"升级为**已验证的永久性结论**，此后不必再复查、不必再提问。

**通道实体已建成（2026-08-17 pm）**：`workspace/metrics/wechat-reads.csv`（5 篇在册）+ 同目录 `README.md` 填写说明。

**验收判据同步收紧**：`gen_dashboard.py` 的 C4 原本认"本文件存在且含『结论：』"即打勾——
那等于**系统自己写一份可行性文档就点亮了一条验收标准**（W-008／T-024 点名的自我确认闭环）。
本场改为只认 `wechat-reads.csv` 里**至少一行有实测 `reads` 数字**，四场景实测见 journal/2026-08-17-pm.md。
**代价是 C4 当场由 ✓ 回落为 ✗**，这是诚实的取值：通道有了，数据一个没有。
