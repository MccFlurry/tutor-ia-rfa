declare module 'html2pdf.js' {
  interface Html2PdfInstance {
    from(el: HTMLElement | string): Html2PdfInstance
    set(opts: Record<string, unknown>): Html2PdfInstance
    save(filename?: string): Promise<void>
    toPdf(): Html2PdfInstance
    get(name: string): Html2PdfInstance
    outputPdf(type?: string): Promise<unknown>
    // html2pdf's worker is a chainable thenable: `.then` returns the worker,
    // not a real Promise. Callback receives any (jsPDF instance for 'pdf').
    then(onFulfilled: (value: any) => unknown): Html2PdfInstance
  }
  const html2pdf: () => Html2PdfInstance
  export default html2pdf
}
