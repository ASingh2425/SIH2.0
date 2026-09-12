import { BoundingRect, DOMNodeDescriptor } from '../types/context';

export class DOMExtractor {
  private nodeMap = new Map<string, HTMLElement>();
  private nodeCounter = 0;

  /**
   * Captures the live DOM and Accessibility hierarchy within current tab bounds.
   */
  public extractDOMContext(): { nodes: DOMNodeDescriptor[]; nodeMap: Map<string, HTMLElement> } {
    this.nodeMap.clear();
    this.nodeCounter = 0;

    const rawNodes: DOMNodeDescriptor[] = [];
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_ELEMENT,
      {
        acceptNode: (node: Node) => {
          const el = node as HTMLElement;
          if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE' || el.tagName === 'NOSCRIPT') {
            return NodeFilter.FILTER_REJECT;
          }
          const rect = el.getBoundingClientRect();
          if (rect.width === 0 && rect.height === 0) {
            return NodeFilter.FILTER_SKIP;
          }
          return NodeFilter.FILTER_ACCEPT;
        },
      }
    );

    let currentNode = walker.nextNode();
    while (currentNode) {
      const el = currentNode as HTMLElement;
      const nodeId = `el_${++this.nodeCounter}`;
      this.nodeMap.set(nodeId, el);

      const bounds = this.getBounds(el);
      const isInput = el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT';
      const isClickable =
        el.tagName === 'BUTTON' ||
        el.tagName === 'A' ||
        el.getAttribute('role') === 'button' ||
        el.onclick !== null;

      let textContent = '';
      if (isInput) {
        textContent = (el as HTMLInputElement).value || el.getAttribute('placeholder') || '';
      } else if (el.children.length === 0) {
        textContent = el.innerText.trim();
      }

      const attributes: Record<string, string> = {};
      for (let i = 0; i < el.attributes.length; i++) {
        const attr = el.attributes[i];
        if (!['style', 'class', 'onclick'].includes(attr.name)) {
          attributes[attr.name] = attr.value;
        }
      }

      rawNodes.push({
        nodeId,
        tagName: el.tagName.toLowerCase(),
        role: el.getAttribute('role') || undefined,
        text: textContent,
        placeholder: el.getAttribute('placeholder') || undefined,
        inputType: (el as HTMLInputElement).type || undefined,
        nameAttr: el.getAttribute('name') || undefined,
        idAttr: el.getAttribute('id') || undefined,
        attributes,
        bounds,
        isInput,
        isClickable,
        isVisible: true,
      });

      currentNode = walker.nextNode();
    }

    return { nodes: rawNodes, nodeMap: this.nodeMap };
  }

  private getBounds(el: HTMLElement): BoundingRect {
    const rect = el.getBoundingClientRect();
    return {
      x: Math.round(rect.left),
      y: Math.round(rect.top),
      width: Math.round(rect.width),
      height: Math.round(rect.height),
    };
  }
}
