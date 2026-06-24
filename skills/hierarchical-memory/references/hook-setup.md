# Hook 配置详情

## 脚本位置
`<hermes-user-path>\AppData\Local\hermes\hooks\mem-sync-check.py`

## config.yaml 配置
```yaml
hooks:
  post_tool_call:
    - command: python C:/Users/86198/AppData/Local/hermes/hooks/mem-sync-check.py
      timeout: 5
  pre_llm_call:
    - command: python C:/Users/86198/AppData/Local/hermes/hooks/mem-sync-check.py
      timeout: 5
hooks_auto_accept: true
```

## 事件流

```
post_tool_call (每次工具调用后)
  ├─ write_file/patch/skill_manage/memory 写 hermes 目录
  │    → 写 .mem_sync_needed 标记文件
  └─ read_file 读 reference/ 文件
       → 正则匹配 [参考] 行 → count += 1

pre_llm_call (下轮 LLM 调用前)
  └─ .mem_sync_needed 存在
       → 注入 JSON: {"context": "[自检] …"}
       → 删除标记文件
```

## 正则

参考记忆行匹配：
```
^\[参考\]\s*{filename}\s*\|\s*count=(\d+)
```
