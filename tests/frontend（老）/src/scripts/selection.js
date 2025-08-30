// selection.js
export class SelectionTool {
    constructor(svg) {
        this.svg = svg; // SVG DOM 元素
        this.points = []; // 存储鼠标路径的点
        this.isDrawing = false; // 是否正在绘制
        this.selectionPath = null; // 当前绘制的路径元素
        this.selectedIds = []; // 存储被选中的元素id
        this.originalStyles = {}; // 存储所有元素原始样式
        this.selectType = "single-time" // single-time: 单次模式, union: 并集模式， intersection: 交集模式， difference: 差集模式
        this.scoreRange = [100, 100]; // 滑动条区间
        this.sortedScores = [];
        this.initializeElements();
    }

    // 初始化所有元素的原始样式
    initializeElements() {
        const elements = this.svg.selectAll("[connotation]").nodes();
        this.originalStyles = {};
        this.scores = [];

        elements.forEach((element, i) => {
            // 获取 highlight_score 属性
            const scoreAttr = element.getAttribute('highlight_score');
            const score = scoreAttr ? parseFloat(scoreAttr) : 0;
            
            // 存储分数和元素
            this.scores.push({ id: i, score });
            
            // 原始样式存储保持不变
            this.originalStyles[i] = {
                stroke: element.getAttribute("stroke") || "none",
                strokeWidth: Number(element.getAttribute("stroke-width")) || 1,
                fill: element.getAttribute("fill") || "none"
            }
        });

        // 按分数升序排序（从高到低）
        this.sortedScores = [...this.scores].sort((a, b) => b.score - a.score);
        //console.log(this.sortedScores)
    }
    
    setScoreRange(range) {
        this.scoreRange = [...range];
    }
    
    // 开始绘制
    startDrawing(event) {
        if (event.button !== 0) return; // 只响应鼠标左键
        this.isDrawing = true;
    
        // 计算相对于 SVG 的坐标
        const { scaleX, scaleY } = this.getScaleFactor();
        const svgRect = this.svg.node().getBoundingClientRect();
        const x = (event.clientX - svgRect.left) / scaleX;
        const y = (event.clientY - svgRect.top) / scaleY;
        this.points = [[x, y]];

        // 删除之前的路径
        if (this.selectionPath) {
            this.selectionPath.remove();
        }

        this.selectionPath = this.svg.append("path")
            .attr("stroke", "blue")
            .attr("stroke-width", 2)
            .attr("fill", "none")
            .attr("pointer-events", "none"); // 禁止鼠标事件干扰

        // 禁止文字高亮
        document.body.style.userSelect = "none";
    }

    // 绘制过程中更新路径
    updateDrawing(event) {
        if (!this.isDrawing) return;
        // 获取 SVG 元素的位置
        const svgRect = this.svg.node().getBoundingClientRect();
        const { scaleX, scaleY } = this.getScaleFactor();
    
        // 计算相对于 SVG 的坐标
        const x = (event.clientX - svgRect.left) / scaleX;
        const y = (event.clientY - svgRect.top) / scaleY;
        this.points.push([x, y]);
        const pathData = this.points.map(p => `L${p[0]},${p[1]}`).join(" ");
        this.selectionPath.attr("d", `M${this.points[0][0]},${this.points[0][1]} ${pathData}`);
    }

    // 结束绘制
    endDrawing() {
        if (!this.isDrawing) return;
        this.isDrawing = false;
        this.points.push(this.points[0]); // 自动连接首尾
        const pathData = this.points.map(p => `L${p[0]},${p[1]}`).join(" ");
        this.selectionPath.attr("d", `M${this.points[0][0]},${this.points[0][1]} ${pathData}`)
            .attr("fill", "rgba(0, 255, 0, 0.3)") // 半透明填充
            .attr("fill-opacity", 0.3);

        // 恢复文字高亮
        document.body.style.userSelect = "";
        // 更新选中元素数组
        const currentSelectedIds = this.checkElementsWithinShape();
        this.updateSelection(currentSelectedIds);
    }

    updateSelection(currentSelectedIds) {
        if (this.selectType === "single-time") {
            // 单次选择，直接替换当前选区
            this.selectedIds = structuredClone(currentSelectedIds);
        } else if (this.selectType === "union") {
            // 并集操作
            this.selectedIds = [...new Set([...this.selectedIds, ...currentSelectedIds])]
        } else if (this.selectType === "intersection") {
            // 交集操作
            const intersection = [];
            for (const id of this.selectedIds) {
                if (currentSelectedIds.includes(id)) {
                    intersection.push(id);
                }
            }
            this.selectedIds = intersection;
        } else if (this.selectType === "difference") {
            // 差集操作
            const difference = [];
            for (const id of this.selectedIds) {
                if (!currentSelectedIds.includes(id)) {
                    difference.push(id);
                }
            }
            this.selectedIds = difference;
        }
        // 更新高亮元素
        this.highlightSelectedElements();
    }

    // 检查形状内的元素
    checkElementsWithinShape() {
        const localSelectedIds = [];
        const elements = this.svg.selectAll("[connotation]");
        
        console.log(elements.nodes()[0])
        //console.log(this.originalStyles)
        elements.each((d, i, nodes) => {
            const element = nodes[i];
            const center = this.getCenter(element);
            if (this.isPointInPolygon(center)) {
                localSelectedIds.push(i)
            }
        });
        
        //console.log("Selected Elements:", localSelectedIds);
        return localSelectedIds;
    }

    highlightSelectedElements() {
        const elements = this.svg.selectAll("[connotation]");
        elements.each((d, i, nodes) => {
            const element = nodes[i];
            const original = this.originalStyles[i];
            // 初始化样式
            element.setAttribute("stroke", original.stroke);
            element.setAttribute("stroke-width", original.strokeWidth);
            element.setAttribute("fill", original.fill);

            // 分数区间高亮判断
            if (this.isInScoreRange(i)) {
                element.setAttribute("fill", "gold"); // 使用金色填充
            }

            // 选区高亮判断
            if (this.selectedIds.includes(i)) {
                element.setAttribute("stroke", "green");
                element.setAttribute("stroke-width", 2);
            }
        });
    }

    getCenter(element){
        const { scaleX, scaleY } = this.getScaleFactor();
        const svgRect = this.svg.node().getBoundingClientRect();
        const rect = element.getBoundingClientRect();
        // 计算圆形的中心点坐标（相对于 SVG）
        const x = rect.left - svgRect.left;
        const y = rect.top - svgRect.top;
        const centerX = (x + rect.width / 2) / scaleX;
        const centerY = (y + rect.height / 2) / scaleY;
        
        return [centerX, centerY];
    }

    // 判断点是否在多边形内（射线法）
    isPointInPolygon(point) {
        let isInside = false;
        
        const x = point[0], y = point[1];
        for (let i = 0, j = this.points.length - 1; i < this.points.length; j = i++) {
            const xi = this.points[i][0], yi = this.points[i][1];
            const xj = this.points[j][0], yj = this.points[j][1];
            const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / (yj - yi) + xi);
            if (intersect) isInside = !isInside;
        }
        return isInside;
    }

    isInScoreRange(id) {
        const [minSlider, maxSlider] = this.scoreRange;
        const total = this.sortedScores.length;
        
        // 转换为实际百分比范围（示例中要求的逻辑）
        const actualMin = 100 - maxSlider;
        const actualMax = 100 - minSlider;
        
        // 计算索引范围
        const minIndex = Math.floor((actualMin / 100) * total);
        const maxIndex = Math.ceil((actualMax / 100) * total);

        // 查找当前元素的索引位置
        const elementIndex = this.sortedScores.findIndex(e => e.id === id);
        
        return elementIndex >= minIndex && elementIndex <= maxIndex;
    }
    
    getSelection(){
        const result = []; // 用于存储最终的结果对象
        const elements = this.svg.selectAll("[connotation]");
        // 遍历 this.selectedIds 的所有值
        for (const id of this.selectedIds) {
            if (this.selectedIds.includes(id)) {
                const value = elements.nodes()[id].getAttribute("connotation");
    
                // 判断是否可以将字符串解析为对象
                try {
                    const parsedValue = JSON.parse(value);
                    result.push({'id':id, ...parsedValue}); // 如果解析成功，添加解析后的对象
                } catch (error) {
                    result.push({'id':id, ...value}); // 如果解析失败，保持原字符串
                }
            }
        }
    
        return result; // 返回结果数组
    }
    getScaleFactor() {
        const svgNode = this.svg.node();
        const rect = svgNode.getBoundingClientRect();
        return {
            scaleX: rect.width / svgNode.clientWidth,
            scaleY: rect.height / svgNode.clientHeight
            // 真 / 虚
        };
    }
}