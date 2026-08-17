/* modules/docreport.js — V142 Thống kê tài liệu họp: tên file gốc, chỉ loại trừ giấy mời thuần */
(function(){
  function E(s){return (typeof esc==='function'?esc(s):String(s==null?'':s).replace(/[&<>\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[m])));}
  function fState(){APP.docsReport=APP.docsReport||{loaded:false,rows:[],stats:{},filters:null};return APP.docsReport;}
  function defaultFilters(){
    const now=new Date();
    const first=new Date(now.getFullYear(),now.getMonth(),1);
    const last=new Date(now.getFullYear(),now.getMonth()+1,0);
    return {dateFrom:dateInputValue_(first),dateTo:dateInputValue_(last),keyword:'',leader:'all',status:'all',docStatus:'ALL',includeCancelled:false,limit:500};
  }
  function filters(){const st=fState();st.filters=st.filters||defaultFilters();return st.filters;}
  function docStatusLabel(s){return {ALL:'Tất cả',ASSIGNED:'Có giao chuẩn bị',OK:'Đã gắn tài liệu',MISSING:'Thiếu tài liệu',NO_ASSIGN:'Chưa giao chuẩn bị'}[String(s||'ALL').toUpperCase()]||s;}
  function readFilters(){
    const f=filters();
    ['dateFrom','dateTo','keyword','leader','status','docStatus','limit'].forEach(k=>{const el=$('docRpt_'+k); if(el) f[k]=el.value;});
    const inc=$('docRpt_includeCancelled'); if(inc) f.includeCancelled=!!inc.checked;
    f.limit=Math.max(1,Math.min(1000,Number(f.limit)||500));
    fState().filters=f;
    return f;
  }
  async function loadReport(force){
    const f=readFilters();
    const payload={dateFrom:f.dateFrom,dateTo:f.dateTo,keyword:f.keyword,leader:f.leader,status:f.status,docStatus:f.docStatus,includeCancelled:f.includeCancelled,limit:f.limit};
    const st=fState();
    if(!force){
      const cached=fastCacheGet('meetingDocsReport',payload,2*60*1000);
      if(cached){st.rows=cached.rows||[];st.stats=cached.stats||{};st.loaded=true;return cached;}
    }
    const res=await api('getMeetingDocsReport',payload);
    st.rows=res.rows||[];st.stats=res.stats||{};st.serverFilters=res.filters||{};st.loaded=true;
    fastCacheSet('meetingDocsReport',payload,{rows:st.rows,stats:st.stats,filters:st.serverFilters});
    return res;
  }
  window.docsReportReset=function(){APP.docsReport={loaded:false,rows:[],stats:{},filters:defaultFilters()};renderMeetingDocsReport(true);};
  window.renderMeetingDocsReport=async function(force=false){
    const box=$('screen-docsReport'); if(!box)return;
    const f=filters();
    box.innerHTML=`<div class="doc-report-shell">
      <div class="doc-report-hero"><div><h2>📎 Thống kê tài liệu họp</h2><p>Cột "Đính kèm" cho biết đơn vị được giao chuẩn bị đã nộp tài liệu hay chưa. Bấm vào nội dung lịch để xem chi tiết tài liệu. Báo cáo gồm cả lịch giao ban, tự động loại trừ lịch trực ban.</p></div><div class="doc-report-actions"><button class="btn sm" onclick="renderMeetingDocsReport(true)">↻ Tải lại</button><button class="btn primary sm" onclick="exportMeetingDocsReportExcel()">⬇ Xuất Excel</button></div></div>
      <div class="doc-report-toolbar">
        <label>Từ ngày<input id="docRpt_dateFrom" type="date" value="${E(f.dateFrom||'')}"></label>
        <label>Đến ngày<input id="docRpt_dateTo" type="date" value="${E(f.dateTo||'')}"></label>
        <label>Từ khóa<input id="docRpt_keyword" type="search" value="${E(f.keyword||'')}" placeholder="Nội dung, đơn vị, lãnh đạo..." onkeydown="if(event.key==='Enter')renderMeetingDocsReport(true)"></label>
        <label>Lãnh đạo<select id="docRpt_leader"><option value="all">Tất cả lãnh đạo</option>${leaderOptions(f.leader||'all')}</select></label>
        <label>Trạng thái<select id="docRpt_status"><option value="all">Tất cả</option>${optionsAny(['MEETING_STATUS','TRANG_THAI_LICH'],f.status||'all')}</select></label>
        <label>Tình trạng TL<select id="docRpt_docStatus"><option value="ALL" ${f.docStatus==='ALL'?'selected':''}>Tất cả</option><option value="ASSIGNED" ${f.docStatus==='ASSIGNED'?'selected':''}>Có giao chuẩn bị</option><option value="OK" ${f.docStatus==='OK'?'selected':''}>Đã gắn tài liệu</option><option value="MISSING" ${f.docStatus==='MISSING'?'selected':''}>Thiếu tài liệu</option><option value="NO_ASSIGN" ${f.docStatus==='NO_ASSIGN'?'selected':''}>Chưa giao chuẩn bị</option></select></label>
        <label>Giới hạn<input id="docRpt_limit" type="number" min="1" max="1000" value="${E(f.limit||500)}" style="width:92px;min-width:92px"></label>
        <label class="doc-check"><input id="docRpt_includeCancelled" type="checkbox" ${f.includeCancelled?'checked':''}> Kể cả lịch hủy</label>
        <button class="btn primary sm" onclick="renderMeetingDocsReport(true)">🔎 Lọc</button><button class="btn ghost sm" onclick="docsReportReset()">Đặt lại</button>
      </div>
      <div id="docReportContent"><div class="loading"><div class="spin"></div><span>Đang tải thống kê tài liệu họp...</span></div></div>
    </div>`;
    try{await loadReport(force || !fState().loaded);renderContent();}
    catch(e){const c=$('docReportContent');if(c)c.innerHTML=`<div class="doc-report-note err">${E((e&&e.message)||e)}<br>Cần cập nhật Code.gs bản v142 và deploy Web App phiên bản mới. Nếu vẫn timeout, giảm Giới hạn xuống 100–200 rồi lọc theo khoảng ngày ngắn hơn.</div>`;}
  };
  function renderContent(){
    const c=$('docReportContent');if(!c)return;
    const st=fState(),rows=st.rows||[],s=st.stats||{};
    c.innerHTML=`<div class="doc-stat-grid">${stat('Tổng lịch',s.total||0)}${stat('Có giao chuẩn bị',s.assigned||0)}${stat('Đã đính kèm',s.withFiles||0)}${stat('Chưa đính kèm',s.missing||0,'danger')}</div>
    <div class="doc-report-note">Đơn vị được giao chuẩn bị mà chưa nộp tài liệu chuyên môn nào sẽ hiện "Chưa đính kèm". Giấy mời/thư mời thuần không tính là tài liệu đã nộp.</div>
    <div class="doc-table-wrap">${rows.length?table(rows):'<div class="doc-empty">Không có lịch phù hợp điều kiện lọc.</div>'}</div>`;
  }
  function stat(label,val,cls){return `<div class="doc-stat ${E(cls||'')}"><b>${E(val)}</b><span>${E(label)}</span></div>`;}
  function table(rows){return `<table class="doc-report-table"><thead><tr><th>STT</th><th>Ngày/Giờ</th><th>Nội dung lịch</th><th>Lãnh đạo</th><th>Đơn vị chuẩn bị</th><th>Đính kèm</th><th>Ghi chú</th></tr></thead><tbody>${rows.map(row).join('')}</tbody></table>`;}
  function row(r,i){
    const counted=Number(r.countedFileCount!=null?r.countedFileCount:(r.fileCount||0));
    const status=r.missingDocs?'<span class="doc-status missing">✕ Chưa đính kèm</span>':(counted>0?`<span class="doc-status ok">✓ Đã đính kèm (${E(counted)})</span>`:'<span class="doc-status none">— Chưa giao CB</span>');
    const gb=r.isGiaoBan?'<span class="doc-tag">Giao ban</span> ':'';
    return `<tr><td class="mono" style="text-align:center">${i+1}<br>${E(r.meetingId||'')}</td><td class="nowrap"><b>${E(dateVN(r.ngayBatDau||r.ngayHienThi))}</b><br><span class="doc-meta">${E(r.thu||'')} · ${E(r.gioBatDau||'')}${r.gioKetThuc?'–'+E(r.gioKetThuc):''}</span></td><td class="doc-clickable" onclick='openDetail(${jss(r.meetingId||'')})'><div class="doc-title">${gb}${E(r.noiDung||'')}</div><span class="doc-meta">${E(typeLabel(r.loaiLich||''))} · ${E(statusLabel(r.trangThai||''))}</span><span class="doc-meta">📍 ${E(r.diaDiem||'')}</span></td><td>${E(r.chuTri||'')}<span class="doc-meta">${E(r.lanhDaoLienQuan||'')}</span></td><td><b>${E(r.donViChuanBi||'')}</b></td><td>${status}</td><td>${E(r.ghiChu||'')}</td></tr>`;
  }
  window.exportMeetingDocsReportExcel=function(){
    const rows=(fState().rows)||[]; if(!rows.length){alert('Không có dữ liệu để xuất Excel.');return;}
    const f=filters();
    const cols=['STT','Mã lịch','Ngày','Thứ','Giờ','Loại lịch','Giao ban','Nội dung','Địa điểm','Chủ trì','Lãnh đạo liên quan','Đơn vị chuẩn bị','Tình trạng tài liệu','Số TL được tính','Tổng file','Số file không tính','Tên tài liệu','Người upload','Thời điểm upload','Phạm vi xem','Link tài liệu','Ghi chú'];
    const safe=v=>String(v==null?'':v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br>');
    const th=v=>'<th style="background:#0f4c81;color:#fff;border:1px solid #0f4c81;padding:6px 7px;text-align:center">'+safe(v)+'</th>';
    const cell=(v,extra='')=>'<td style="vertical-align:top;border:1px solid #d9e3ec;padding:5px 7px;'+extra+'">'+safe(v)+'</td>';
    const trs=[];
    rows.forEach((r,idx)=>{const files=(r.files&&r.files.length)?r.files:[{}];files.forEach(file=>{const red=r.missingDocs?'background:#fee2e2;color:#991b1b;font-weight:bold;':'';trs.push('<tr>'+[idx+1,r.meetingId,dateVN(r.ngayBatDau||r.ngayHienThi),r.thu,(r.gioBatDau||'')+(r.gioKetThuc?' - '+r.gioKetThuc:''),typeLabel(r.loaiLich||''),r.isGiaoBan?'Có':'',r.noiDung,r.diaDiem,r.chuTri,r.lanhDaoLienQuan,r.donViChuanBi,r.missingDocs?'THIẾU TÀI LIỆU':((r.countedFileCount||r.fileCount)>0?'Đã có tài liệu được tính':'Chưa giao chuẩn bị'),r.countedFileCount!=null?r.countedFileCount:(r.fileCount||0),r.totalFileCount!=null?r.totalFileCount:(r.fileCount||0),r.excludedFileCount||0,(file.excludeFromPrep?'[KHÔNG TÍNH] ':'')+(file.displayFileName||file.fileDisplayName||file.fileName||''),file.uploadedBy||'',file.uploadedAt||'',file.fileVisibilityLabel||'',file.fileUrl||'',r.ghiChu||''].map(v=>cell(v,red)).join('')+'</tr>');});});
    const filterText='Từ '+(f.dateFrom||'')+' đến '+(f.dateTo||'')+' | Tình trạng: '+docStatusLabel(f.docStatus)+' | Từ khóa: '+(f.keyword||'Tất cả')+' | Đã loại trừ lịch trực ban | Giấy mời/tài liệu mời thuần không tính; tài liệu chuyên môn do Văn phòng upload thay đơn vị vẫn được tính';
    const html='<!doctype html><html><head><meta charset="UTF-8"></head><body><h2 style="font-family:Arial;color:#063a63">THỐNG KÊ TÀI LIỆU HỌP HQKV8</h2><p style="font-family:Arial">'+safe(filterText)+'</p><table style="border-collapse:collapse;font-family:Arial;font-size:10pt"><thead><tr>'+cols.map(th).join('')+'</tr></thead><tbody>'+trs.join('')+'</tbody></table></body></html>';
    const blob=new Blob(['\ufeff',html],{type:'application/vnd.ms-excel;charset=utf-8'});
    const a=document.createElement('a'),now=new Date(),pad=n=>String(n).padStart(2,'0');
    a.href=URL.createObjectURL(blob);a.download='Thong_ke_tai_lieu_hop_HQKV8_'+now.getFullYear()+pad(now.getMonth()+1)+pad(now.getDate())+'_'+pad(now.getHours())+pad(now.getMinutes())+'.xls';document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},500);
  };
})();
