# 沉溪地研 · 钻孔隐状态序列复核

为14人地学数据组锁定完整1米孔段与高斯HMM模型，分开核对点态平滑后验和Viterbi整条MAP路径，再由地学编辑批准归档。

## 真实场景与六实体

上游 `shenxi_logs_202611.csv` 为SX-01/02/03三孔各160点模拟测井。团队原用表格逐点硬阈值划分，噪声造成状态跳变、点态概率与全路径被混为一谈、缺采样后直接串链。本工程替代完整性核查、模型登记/命名修订、孔段与模型快照、异步解码和复核；下游地研档案组读取批准的模型状态序列CSV。输出是给定模型下隐状态，不是真实地层或地质安全判断。

BoreholeDataset测井、StateModel人工配置模型、SequenceStudy锁定孔段、DecodeRun运行、LayerReview复核、Report报告六实体贯穿。六页：孔段档案、完整测井、状态模型、锁定与解码、后验与路径、地学复核，另有登录。两页复用BoreholeTrack、SequenceSummary、ModelMatrix。

## 快速启动

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

前端 http://localhost:18238 ，API http://localhost:19238/docs ，PostgreSQL17738。Compose name=stratum-hidden，恰好frontend/backend/worker/db/redis五服务，均有healthcheck和依赖健康门禁。Nginx反代/api与SPA回落，健康检查127.0.0.1。数据库/Redis/共享JSON和CSV分别使用命名卷。清理 `docker compose down -v --remove-orphans`。

| 角色 / 账号 | 页面 | 权限与典型动作 |
|---|---|---|
| admin@shenxi.test / 孔段复核地学编辑 | 六页与审计 | 读写、批准/退回、核查模型状态解释 |
| analyst@shenxi.test / 测井序列分析员 | 测井、模型、研究、结果、复核 | 导入、配置/修订模型、运行、提审、生成批准报告 |
| viewer@shenxi.test / 地研档案阅览员 | 六页只读 | 查看与下载已批准CSV |

演示密码均为 `Stratum2026!`。PBKDF2密码、HS256 JWT、角色依赖、actor审计、全局错误恢复与最多10个排队/运行任务。默认密钥与账号仅供本地演示。

## 一天的孔段剧本

1. 09:00 导入shenxi_logs_202611.csv，3孔×160点=480行，深度100—259m。
2. 09:05 检查每孔输入顺序和1米间距；重复、缺层、倒序不自动拼接。
3. 09:10 核查三态均值45/70/98、方差16/25/16、初始和转移，人工命名为低/中/高响应态。
4. 09:15 选择SX-01整个160点孔段，锁定模型修订、读数、概率与名称快照，保存SHA256。
5. 09:20 提交Redis，独立Python worker运行对数域前向后向与Viterbi回溯，结果落PostgreSQL和共享JSON。
6. 09:25 沿深度查看读数、三态后验、点态argmax与整条MAP，核查对数分数与回溯前驱。
7. 09:30 模型后来修订为v2时，旧研究和报告仍引用v1，分析员提交地学复核。
8. 09:40 编辑批准后下载CSV，保留孔段、旧模型名称/概率/参数、点态后验、路径与回溯。

## 完整孔段与模型输入

CSV列borehole,depth_m,value，truth可选且仅作模拟参考。孔ID为1—30位字母数字下划线连字符。深度[0,10000]m，每孔按输入严格1m递增（容差1e-9），至少3点、最多1000点；总量5000行、最多8孔。读数有限且绝对值≤1e6，短行/空值/NaN/Inf拒绝，缺失不当0，也不跨缺层串链。研究选择整个已校验孔段，无静默插值或隐式分段。

模型JSON为states:[{id,name,mean,variance}]、initial数组、transition二维数组。K=2—4，ID唯一，人工名称1—30字，均值有限且绝对值≤1e6，方差在[1e-8,1e8]且为正。初始与转移每行概率有限、[0,1]、行和在1e-10内为1；仅在这个浮点容差内按行和规范化。允许精确0，用−∞计算，不加平滑伪计数。配置状态顺序决定索引与同分优先级。

没有EM训练、真实地层标签学习或自动命名。truth只保留参考，既不入发射/先验/转移，也不用于参数估计、状态解释或准确率承诺。

## 稳定前向后向

高斯log发射 ℓ_tj=−½[log(2π)+log(var_j)+(x_t−μ_j)²/var_j]。先减每个时刻公共max C_t，得到相对发射e_tj，再与小的初始/转移分数相加，避免巨大公共负密度抹去先验差别。

前向用logsumexp与每步相对scale c_t：α_tj=e_tj+logsumexp(α_(t−1)i+log A_ij)−c_t；总观测log密度为ΣC_t+Σc_t。后向β_ti=logsumexp(log A_ij+e_(t+1)j+β_(t+1)j)−c_(t+1)，仅使用相对scale。后验逐行对α+β作logsumexp归一，再作微小浮点质量规范化，行和1。不可达状态后验0，对数证据以null表示−∞，不输出NaN。

后验使用完整孔段未来观测，是离线平滑。每点argmax是该深度的边际最可能状态，不等于整条最可能路径，逐点拼接甚至可能违反零转移。

## Viterbi整条MAP

δ_tj=e_tj+max_i(δ_(t−1)i+log A_ij)，每步减公共max并独立累计offset；记录每个状态最佳前驱，从最终最佳状态逐步回溯。精确同分按配置状态顺序优先。保存path、backpointers、相对log分数与offset，不能拿后验argmax代替。

总MAP分数是路径与连续观测的联合对数密度，不是离散概率。返回log_joint_density；兼容键log_probability表示同一联合对数密度。整路径后验log P(path|观测)通过相对MAP分数减相对观测log密度得到，先抵消公共Gaussian offset，避免两个巨大数相减。UI和CSV明确区分这三种量，未将低似然指数化。

## 版本、快照与报告

StateModel修订PATCH递增revision；研究保存完整孔段读数、truth参考、状态ID/人工名称/参数/初始/转移/修订号及源文件的规范JSON SHA256。worker仅读研究快照，后续模型编辑或数据集改名不改旧结果。报告固定引用批准运行及其旧版本；CSV含模型参数、转移、后验、点态/路径、模拟参考与回溯前驱。未批准生成被拒绝，重复决定409。

## 工程与本地开发

| 层 | 技术 |
|---|---|
| 前端 | React18 / TypeScript5.7 / Vite6 / Nginx1.28 |
| 后端 | Python3.12 / FastAPI / psycopg3 |
| 核心数值 | Python math自实现logsumexp、前向后向、Viterbi |
| 异步与数据库 | Redis7.4 / 独立worker / PostgreSQL16 |

81个代码源文件，src内77个职责文件。backend/src含routes/controllers/services/models/schemas/middlewares/utils/constants/config；frontend/src含api/stores/types/components/common/hooks/pages/router/utils/constants。DDL在backend/migrations，advisory lock保护首次建表。科学数值使用Python float双精度并在PostgreSQL JSON文本载荷无显示舍入往返，日志中的−∞用null编码。配套requirements沿用已测依赖，NumPy不是本项目核心算法依赖。

Seed固定2409，3孔各160点，配置三态均值/方差与持久转移，含少量模拟测量扰动；truth为模拟生成态，仅参考。SEED_DEMO=true自动seed，失败记日志不阻断，自然键insert-only，重复不新增、不覆盖用户修改。普通SX-01种子两种标签可能完全一致；独立四点反例在验收中明确呈现两种目标差异。

环境DATABASE_URL、REDIS_URL、JWT_SECRET、SEED_DEMO、TASK_MODE、ARTIFACT_DIR与端口/DB_PASSWORD见.env.example。本地配置PG/Redis，pip install backend/requirements.txt后uvicorn src.main:app --reload；前端npm ci && npm run dev，经/api反代。package与lock精确复用已测配套版本，仅改根项目名。

枚举：backend/src/constants/enums.py(Role/RunStatus/ReviewStatus)、domain.py(步长/配额/假设)；frontend/src/constants/enums.ts(角色/状态)。通用共享PageTitle/Notice/StatusBadge，业务共享轨迹/模型矩阵，hooks/useResource/useSession、utils/chart/format。

限制：固定一维高斯和齐次转移假设，不拟合参数，模型失配会造成误导。只处理完整1米孔段，不跨孔、不补缺层；后验是给定模型条件概率，不等于真实岩性确认。浮点极端近同发射仍有有限精度；公共offset和相对分数单独保留。Redis出队强杀不自动重投，JSON载荷无多人乐观锁/迁移回滚。所有真实测试、日志和截图仅在批次test-artifacts/gb-2409。

## License

MIT，见LICENSE。
