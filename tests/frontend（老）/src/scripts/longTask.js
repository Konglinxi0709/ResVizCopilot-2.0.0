import axios from 'axios'

const DEFAULT_POLL_INTERVAL = 1000
const MAX_POLL_ATTEMPTS = 300 // 5分钟超时

export const longTaskRequest = (config) => {
  let progressCallback = null
  let taskId = null
  let pollAttempts = 0
  
  // 创建主请求Promise（修复了async executor问题）
  const mainPromise = new Promise((resolve, reject) => {
    // 初始请求
    axios({
      ...config,
      validateStatus: () => true
    })
      .then(response => {
        if (response.status !== 200 || !response.data?.task_id) {
          throw new Error('Failed to start long task')
        }
        taskId = response.data.task_id
        startPolling(resolve, reject)
      })
      .catch(reject)
  })

  const startPolling = (resolve, reject) => {
    const poll = () => {
      if (pollAttempts++ > MAX_POLL_ATTEMPTS) {
        reject(new Error('Task timeout'))
        return
      }

      axios.get(`/api/downloads/${taskId}`, { baseURL: config.baseURL })
        .then(statusRes => {
          const { status, result, error, progress } = statusRes.data
          
          if (progressCallback && typeof progress === 'number') {
            progressCallback(progress)
          }

          switch (status) {
            case 'completed':
              resolve(result)
              break
            case 'failed':
              reject(new Error(error || 'Task failed'))
              break
            case 'pending':
            case 'processing':
              setTimeout(poll, DEFAULT_POLL_INTERVAL)
              break
          }
        })
        .catch(reject)
    }

    setTimeout(poll, DEFAULT_POLL_INTERVAL)
  }

  // 创建带进度回调的扩展对象
  const extendedPromise = mainPromise
  
  extendedPromise.progress = (callback) => {
    progressCallback = callback
    return extendedPromise
  }
  
  return extendedPromise
}