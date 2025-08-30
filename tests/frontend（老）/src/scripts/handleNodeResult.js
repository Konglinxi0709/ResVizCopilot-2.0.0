export async function handleResult(org_nodes, result) {
  //console.log('前端数据库:', org_nodes)
  //console.log('处理后端数据：', result)
  let newNode = { ...org_nodes }; // 创建 nodes 的副本，避免直接修改原始数据

  // 1. 处理 update_nodes（覆盖替换）
  if (Array.isArray(result?.update_nodes)) {
    newNode = {}; // 清空现有节点
    result.update_nodes.forEach(node => {
      newNode[node.id] = node; // 添加更新后的节点
    });
  }

  // 2. 处理 add_nodes（合并新增）
  if (Array.isArray(result?.add_nodes)) {
    result.add_nodes.forEach(node => {
      newNode[node.id] = node; // 添加新增的节点
    });
  }

  // 3. 处理 del_ids（删除操作）
  if (result?.del_ids?.length > 0) {
    const delSet = new Set(result.del_ids.map(String));
    // 过滤出不需要删除的节点
    const filteredNodes = {};
    for (const id in newNode) {
      if (!delSet.has(id)) {
        filteredNodes[id] = newNode[id];
      }
    }
    newNode = filteredNodes; // 重新赋值
  }
  //console.log('更新后的前端数据库:', newNode)
  // 最后一次性更新 nodes，减少响应式系统的触发次数
  return newNode;
}